import { useEffect, useRef } from "react";
import { Plus, MessageSquare, Trash2, Bot } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { Conversation } from "../hooks/useConversations";

export function ConversationsSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: 0 });
  }, [conversations.length]);

  return (
    <aside
      data-testid="conversations-sidebar"
      className="flex h-full min-h-0 flex-col gap-2 rounded-2xl border border-border/60 bg-card/60 p-2.5 backdrop-blur"
    >
      <button
        type="button"
        data-testid="new-conversation"
        onClick={onNew}
        className="flex items-center gap-2 rounded-xl border border-border/70 bg-background/70 px-3 py-2.5 text-sm font-semibold text-foreground shadow-2xs transition-colors hover:border-primary/40 hover:bg-primary/5 hover:text-primary"
      >
        <Plus size={15} className="text-primary" />
        New conversation
      </button>

      <div ref={listRef} className="scrollbar-none min-h-0 flex-1 space-y-1 overflow-y-auto pt-1">
        {conversations.length === 0 && (
          <div className="flex flex-col items-center gap-2 px-3 py-8 text-center">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-muted text-muted-foreground">
              <Bot size={17} />
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Run a screening to start your first conversation. History stays in this browser.
            </p>
          </div>
        )}

        {conversations.map((c) => (
          <div
            key={c.id}
            data-testid="conversation-item"
            className={cn(
              "group flex cursor-pointer items-center gap-2 rounded-xl px-2.5 py-2 text-sm transition-colors",
              c.id === activeId
                ? "bg-primary/10 text-primary"
                : "text-foreground/80 hover:bg-muted/70",
            )}
            onClick={() => onSelect(c.id)}
          >
            <MessageSquare size={14} className="shrink-0 opacity-70" />
            <span className="min-w-0 flex-1 truncate" title={c.title}>
              {c.title}
            </span>
            <button
              type="button"
              aria-label={`Delete ${c.title}`}
              data-testid="delete-conversation"
              className="shrink-0 rounded-md p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(c.id);
              }}
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>

      <p className="px-2 pb-1 text-[10px] leading-relaxed text-muted-foreground">
        Conversations bind to backend chat sessions; messages sync to your account when signed in.
      </p>
    </aside>
  );
}
