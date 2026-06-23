"use client";

import { SessionSelector } from "@/components/chat/SessionSelector";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * ChatHeader - Minimal status and session utility bar
 * Blends directly into the page layout without looking like a second header block
 */
export function ChatHeader(): React.JSX.Element {
  const {
    userId,
    sessionId,
    handleSessionSwitch,
    handleCreateNewSession,
  } = useChatContext();

  return (
    <div className="relative z-10 flex-shrink-0 bg-transparent py-2.5 px-4 md:px-8">
      <div className="max-w-7xl mx-auto w-full flex items-center justify-between gap-4">
        {/* Left side - Minimal status indicator */}
        <div className="flex items-center gap-2.5">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest hidden sm:inline">Active Copilot Session</span>
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest sm:hidden">Active</span>
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </div>

        {/* Right side - Session Selector dropdown */}
        <div className="flex items-center gap-4">
          {userId && (
            <div className="flex items-center gap-2">
              <SessionSelector
                currentUserId={userId}
                currentSessionId={sessionId}
                onSessionSelect={handleSessionSwitch}
                onCreateSession={handleCreateNewSession}
                className="text-xs"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
