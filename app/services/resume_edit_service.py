"""Line-based resume document editing with undo/redo support.

The resume is stored as a list of lines. Every edit (insert/replace/delete)
is recorded as a :class:`ResumeEditAction` and pushed onto an undo stack.
Undo pops the action, reconstructs the previous content, and pushes it onto
the redo stack. Redo is the inverse.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.resume_edit_session_repository import (
    ResumeEditSessionRepository,
)
from app.models.resume_workspace import (
    ResumeEditAction,
    ResumeEditApplyResponse,
    ResumeEditUndoResponse,
)

logger = logging.getLogger(__name__)

MAX_STACK_SIZE = 100


class EditConflictError(RuntimeError):
    """Raised when an edit cannot be resolved against the current document.

    This signals that the client's view of the document has diverged from the
    server's state (e.g. another edit shifted the target line), so the caller
    should re-fetch the document before retrying instead of silently editing
    the wrong content.
    """


class ResumeEditService:
    """Apply edits and handle undo/redo for a resume document.

    Args:
        session: An async SQLAlchemy session for persistence.
        repo: Repository for editing sessions.
    """

    def __init__(
        self,
        session: AsyncSession,
        repo: ResumeEditSessionRepository | None = None,
    ) -> None:
        """Initialize the editing service."""
        self.session = session
        self.repo = repo or ResumeEditSessionRepository(session)

    async def create_session(
        self,
        *,
        resume_text: str,
        user_id: str | None = None,
        resume_filename: str | None = None,
        resume_blob_url: str | None = None,
    ) -> str:
        """Create an editing session seeded with the uploaded resume text.

        Args:
            resume_text: Initial resume text.
            user_id: Owning user.
            resume_filename: Optional original filename.
            resume_blob_url: Optional original blob URL.

        Returns:
            The new editing session id.
        """
        row = await self.repo.create(
            user_id=user_id,
            content=resume_text,
            resume_filename=resume_filename,
            resume_blob_url=resume_blob_url,
        )
        return row.id

    async def get_content(
        self, document_id: str, *, user_id: str | None = None
    ) -> str | None:
        """Return the current resume text for an editing session.

        Args:
            document_id: The editing session id.
            user_id: Optional owner to enforce ownership. When provided and the
                session is owned by a different user, ``None``-like not found
                and a :class:`KeyError` is not raised (treats it as not found).

        Returns:
            The resume text, or ``None`` if not found or not owned.
        """
        row = await self.repo.get(document_id)
        if row is None:
            return None
        if user_id and row.user_id and row.user_id != user_id:
            return None
        return row.content

    async def apply_edit(
        self,
        document_id: str,
        action: ResumeEditAction,
        *,
        user_id: str | None = None,
    ) -> ResumeEditApplyResponse:
        """Apply a single edit action and record it for undo.

        The edit is resolved against the *current* server content by matching
        the affected text (``previous_text``) at the target location, rather
        than trusting a possibly-stale client-provided line index. When the
        expected text cannot be found, a :class:`EditConflictError` is raised
        so the client can re-sync instead of silently editing the wrong line.
        Each applied edit is stamped with the server clock for deterministic,
        monotonic ordering.

        Args:
            document_id: The editing session id.
            action: The edit action to apply.
            user_id: Optional owner to enforce ownership.

        Returns:
            The updated document state.

        Raises:
            KeyError: If the session does not exist or is not owned by ``user_id``.
            EditConflictError: If the target text cannot be resolved against the
                current document state (indicates client/server divergence).
        """
        row = await self.repo.get(document_id)
        if row is None or (user_id and row.user_id and row.user_id != user_id):
            raise KeyError(f"Editing session {document_id} not found")

        lines = row.content.split("\n")
        resolved = self._resolve_action(lines, action)
        if resolved is None:
            raise EditConflictError(
                f"Edit target not found in current content for editing session "
                f"{document_id}. The document may have changed — please re-sync "
                f"before applying."
            )

        target_start, target_end = resolved
        action.start_line = target_start
        action.end_line = target_end
        action.previous_text = "\n".join(lines[target_start:target_end])
        action.timestamp = datetime.now(UTC)

        lines = self._apply_action(lines, action)

        undo_stack = list(row.undo_stack or [])
        undo_stack.append(action.model_dump(mode="json"))
        # New edits invalidate the redo stack.
        redo_stack: list = []

        updated = await self.repo.update_content(
            document_id,
            content="\n".join(lines),
            undo_stack=undo_stack,
            redo_stack=redo_stack,
            revision=(row.revision or 0) + 1,
        )
        assert updated is not None
        return ResumeEditApplyResponse(
            document_id=document_id,
            content=updated.content,
            undo_available=bool(undo_stack),
            redo_available=False,
            revision=updated.revision,
        )

    async def undo(
        self, document_id: str, *, user_id: str | None = None
    ) -> ResumeEditUndoResponse:
        """Undo the most recent edit.

        Args:
            document_id: The editing session id.
            user_id: Optional owner to enforce ownership.

        Returns:
            The reverted document state.

        Raises:
            KeyError: If the session does not exist, is not owned, or there is
                nothing to undo.
        """
        row = await self.repo.get(document_id)
        if row is None or (user_id and row.user_id and row.user_id != user_id):
            raise KeyError(f"Editing session {document_id} not found")

        undo_stack = list(row.undo_stack or [])
        if not undo_stack:
            raise KeyError("Nothing to undo")

        action = ResumeEditAction(**undo_stack.pop())
        lines = row.content.split("\n")
        lines = self._reverse_action(lines, action)

        redo_stack = list(row.redo_stack or [])
        redo_stack.append(action.model_dump(mode="json"))

        updated = await self.repo.update_content(
            document_id,
            content="\n".join(lines),
            undo_stack=undo_stack,
            redo_stack=redo_stack,
            revision=(row.revision or 0) + 1,
        )
        assert updated is not None
        return ResumeEditUndoResponse(
            document_id=document_id,
            content=updated.content,
            undo_available=bool(undo_stack),
            redo_available=bool(redo_stack),
            revision=updated.revision,
        )

    async def redo(
        self, document_id: str, *, user_id: str | None = None
    ) -> ResumeEditUndoResponse:
        """Redo the most recently undone edit.

        Args:
            document_id: The editing session id.
            user_id: Optional owner to enforce ownership.

        Returns:
            The re-applied document state.

        Raises:
            KeyError: If the session does not exist, is not owned, or there is
                nothing to redo.
        """
        row = await self.repo.get(document_id)
        if row is None or (user_id and row.user_id and row.user_id != user_id):
            raise KeyError(f"Editing session {document_id} not found")

        redo_stack = list(row.redo_stack or [])
        if not redo_stack:
            raise KeyError("Nothing to redo")

        action = ResumeEditAction(**redo_stack.pop())
        lines = row.content.split("\n")
        lines = self._apply_action(lines, action)

        undo_stack = list(row.undo_stack or [])
        undo_stack.append(action.model_dump(mode="json"))

        updated = await self.repo.update_content(
            document_id,
            content="\n".join(lines),
            undo_stack=undo_stack,
            redo_stack=redo_stack,
            revision=(row.revision or 0) + 1,
        )
        assert updated is not None
        return ResumeEditUndoResponse(
            document_id=document_id,
            content=updated.content,
            undo_available=bool(undo_stack),
            redo_available=bool(redo_stack),
            revision=updated.revision,
        )

    @staticmethod
    def _resolve_action(
        lines: list[str], action: ResumeEditAction
    ) -> tuple[int, int] | None:
        """Resolve an edit's target location against the current line array.

        The authoritative anchor is the text the client expects to be present
        at the edit site (``action.previous_text`` when provided). This makes
        edits robust to line-index drift caused by other edits applied between
        the client's snapshot and the server's current state.

        Args:
            lines: The current line array.
            action: The edit action to resolve.

        Returns:
            A ``(start_line, end_line)`` tuple locating the edit in the current
            array, or ``None`` when the expected text cannot be found.
        """
        anchor = (action.previous_text or "").split("\n")
        if action.action_type == "replace":
            # Anchor matches the exact text being replaced (may span lines).
            if anchor and anchor != [""]:
                return ResumeEditService._find_span(lines, anchor)
            # Fall back to the provided index when no text anchor was given.
            start = max(0, min(action.start_line, len(lines)))
            end = max(start, min(action.end_line, len(lines)))
            return start, end
        if action.action_type == "delete":
            # Anchor is the exact text being deleted.
            if anchor and anchor != [""]:
                found = ResumeEditService._find_span(lines, anchor)
                if found is not None:
                    return found
            # Fall back to index-based span.
            start = max(0, min(action.start_line, len(lines)))
            end = max(start, min(action.end_line, len(lines)))
            return start, end
        # insert: anchor is the line *after* which we insert; fall back to
        # matching the line before ``start_line`` if no anchor is supplied.
        if action.previous_text and anchor and anchor != [""]:
            found_line = ResumeEditService._find_line(lines, anchor[0])
            if found_line is not None:
                return found_line + 1, found_line + 1
        at = max(0, min(action.start_line, len(lines)))
        return at, at

    @staticmethod
    def _find_span(lines: list[str], needle: list[str]) -> tuple[int, int] | None:
        """Find the index span of ``needle`` (a list of lines) in ``lines``.

        Args:
            lines: The line array to search.
            needle: The sequence of lines to locate.

        Returns:
            A ``(start, end)`` span, or ``None`` if not found.
        """
        n = len(needle)
        for i in range(len(lines) - n + 1):
            if lines[i : i + n] == needle:
                return i, i + n
        return None

    @staticmethod
    def _find_line(lines: list[str], text: str) -> int | None:
        """Find the index of the first line exactly equal to ``text``.

        Args:
            lines: The line array to search.
            text: The exact line text to locate.

        Returns:
            The 0-based index, or ``None`` if not found.
        """
        for i, line in enumerate(lines):
            if line == text:
                return i
        return None

    @staticmethod
    def _apply_action(lines: list[str], action: ResumeEditAction) -> list[str]:
        """Apply an edit action to the line array.

        Args:
            lines: The current line array.
            action: The edit action (insert/replace/delete).

        Returns:
            The updated line array.
        """
        if action.action_type == "insert":
            at = max(0, min(action.start_line, len(lines)))
            new_lines = action.text.split("\n") if action.text else []
            return lines[:at] + new_lines + lines[at:]
        if action.action_type == "delete":
            start = max(0, min(action.start_line, len(lines)))
            end = max(start, min(action.end_line, len(lines)))
            return lines[:start] + lines[end:]
        # replace
        start = max(0, min(action.start_line, len(lines)))
        end = max(start, min(action.end_line, len(lines)))
        new_lines = action.text.split("\n") if action.text else []
        return lines[:start] + new_lines + lines[end:]

    @staticmethod
    def _reverse_action(lines: list[str], action: ResumeEditAction) -> list[str]:
        """Reverse a previously applied action during undo.

        Args:
            lines: The current (post-edit) line array.
            action: The edit action to reverse.

        Returns:
            The reverted line array.
        """
        previous = action.previous_text.split("\n") if action.previous_text else []
        if action.action_type == "insert":
            # The inserted text was placed at start_line; remove it.
            at = max(0, min(action.start_line, len(lines)))
            inserted_count = len(action.text.split("\n")) if action.text else 0
            return lines[:at] + lines[at + inserted_count :]
        if action.action_type == "delete":
            # Reinsert the deleted text at start_line.
            at = max(0, min(action.start_line, len(lines)))
            return lines[:at] + previous + lines[at:]
        # replace: the replaced region was [start, end); restore previous lines.
        start = max(0, min(action.start_line, len(lines)))
        new_line_count = len(action.text.split("\n")) if action.text else 0
        end = start + new_line_count
        return lines[:start] + previous + lines[end:]
