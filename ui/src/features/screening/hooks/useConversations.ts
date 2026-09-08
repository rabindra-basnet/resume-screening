import { useCallback, useEffect, useState } from "react";
import type { ChatMessage } from "@/shared/types";

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  /** Backend chat session id (null until the pipeline binds a chat). */
  chatId: string | null;
  /** Backend edit-session id (null until the pipeline binds one). */
  editSessionId: string | null;
  messages: ChatMessage[];
}

const STORAGE_KEY = "tp-conversations-v1";

function makeId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `c-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function makeTitle(text: string): string {
  const line = text.trim().split("\n")[0] || "New conversation";
  return line.length > 42 ? `${line.slice(0, 42)}…` : line;
}

function load(): Conversation[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function save(conversations: Conversation[]) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  } catch {
    // Storage may be unavailable (private mode / quota) — degrade gracefully.
  }
}

/**
 * Local conversation history for the screening workspace.
 *
 * Conversations are client-side shells that bind to backend chat/edit sessions:
 * the first successful pipeline run fills `chatId`/`editSessionId`, after which
 * messages flow through the backend `/resume-chat` endpoints.
 */
export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = load();
    setConversations(stored);
    setActiveId(stored[0]?.id ?? null);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) save(conversations);
  }, [conversations, hydrated]);

  const active = conversations.find((c) => c.id === activeId) ?? null;

  const createConversation = useCallback((title?: string) => {
    const conv: Conversation = {
      id: makeId(),
      title: title || "New conversation",
      createdAt: new Date().toISOString(),
      chatId: null,
      editSessionId: null,
      messages: [],
    };
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
    return conv;
  }, []);

  const patchConversation = useCallback(
    (id: string, patch: Partial<Conversation>) => {
      setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, ...patch } : c)));
    },
    [],
  );

  const appendMessages = useCallback((id: string, msgs: ChatMessage[]) => {
    setConversations((prev) =>
      prev.map((c) =>
        c.id === id
          ? { ...c, messages: [...c.messages, ...msgs], chatId: c.chatId }
          : c,
      ),
    );
  }, []);

  const appendMessagesForChat = useCallback((chatId: string, msgs: ChatMessage[]) => {
    setConversations((prev) =>
      prev.map((c) => (c.chatId === chatId ? { ...c, messages: [...c.messages, ...msgs] } : c)),
    );
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      setActiveId((cur) => (cur === id ? next[0]?.id ?? null : cur));
      return next;
    });
  }, []);

  const renameConversation = useCallback(
    (id: string, title: string) => {
      const clean = title.trim().slice(0, 60) || "New conversation";
      patchConversation(id, { title: clean });
    },
    [patchConversation],
  );

  return {
    conversations,
    activeId,
    active,
    setActiveId,
    createConversation,
    patchConversation,
    appendMessages,
    appendMessagesForChat,
    deleteConversation,
    renameConversation,
    makeTitle,
  };
}
