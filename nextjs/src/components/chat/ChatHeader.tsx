"use client";

import { Landmark } from "lucide-react";
import { UserIdInput } from "@/components/chat/UserIdInput";
import { SessionSelector } from "@/components/chat/SessionSelector";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * ChatHeader - User and session management interface
 * Extracted from ChatMessagesView header section
 * Handles user ID input and session selection
 */
export function ChatHeader(): React.JSX.Element {
  const {
    userId,
    sessionId,
    handleUserIdChange,
    handleUserIdConfirm,
    handleSessionSwitch,
    handleCreateNewSession,
  } = useChatContext();

  return (
    <div className="relative z-10 flex-shrink-0 border-b border-[#d0d3ea] bg-[#1a1f71] text-[#c8cadf] shadow-sm">
      <div className="max-w-6xl mx-auto w-full flex flex-wrap items-center justify-between gap-4 p-4">
        {/* Left side - App branding */}
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-white text-[#1a1f71] flex items-center justify-center shadow-sm ring-1 ring-white/20">
            <Landmark className="h-[18px] w-[18px]" />
          </div>
          <div>
            <h1 className="text-[15px] font-semibold tracking-[0.02em] text-white">ABC Bank Assistant</h1>
            <p className="text-[11px] text-[#f0a500]">Trusted banking guidance</p>
          </div>
        </div>

        {/* Right side - User controls */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* User ID Management */}
          <UserIdInput
            currentUserId={userId}
            onUserIdChange={handleUserIdChange}
            onUserIdConfirm={handleUserIdConfirm}
            className="text-xs"
          />

          {/* Session Management */}
          {userId && (
            <SessionSelector
              currentUserId={userId}
              currentSessionId={sessionId}
              onSessionSelect={handleSessionSwitch}
              onCreateSession={handleCreateNewSession}
              className="text-xs"
            />
          )}
        </div>
      </div>
    </div>
  );
}
