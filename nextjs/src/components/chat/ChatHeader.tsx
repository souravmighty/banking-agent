"use client";

import { Landmark, User, LogOut } from "lucide-react";
import { SessionSelector } from "@/components/chat/SessionSelector";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * ChatHeader - User and session management interface
 * Extracted from ChatMessagesView header section
 * Handles user authentication display and session selection
 */
export function ChatHeader(): React.JSX.Element {
  const {
    userId,
    sessionId,
    handleSessionSwitch,
    handleCreateNewSession,
    handleSignOut,
    isLoadingAuth,
  } = useChatContext();

  return (
    <div className="relative z-10 flex-shrink-0 border-b border-[#d0d3ea] bg-[#1a1f71] text-[#c8cadf] shadow-sm">
      <div className="max-w-7xl mx-auto w-full flex flex-wrap items-center justify-between gap-4 p-4 md:px-8">
        {/* Left side - App branding */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white text-[#1a1f71] flex items-center justify-center shadow-lg ring-1 ring-white/20 flex-shrink-0">
            <Landmark className="h-6 w-6" />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-base font-bold tracking-tight text-white leading-tight">ABC Bank Assistant</h1>
            <p className="text-[11px] font-semibold text-[#f0a500] uppercase tracking-wider">Secure, trusted banking guidance</p>
          </div>
        </div>

        {/* Right side - User controls */}
        <div className="flex items-center gap-4 flex-wrap sm:flex-nowrap">
          {/* User Authentication Display */}
          {!isLoadingAuth && userId && (
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-medium text-white/80 hidden lg:inline">User:</span>
              <div className="flex items-center gap-2 bg-[#f0a500] px-2.5 py-1 rounded-md border border-[#f0a500]/20 text-[#1a1f71]">
                <User className="w-3 h-3" />
                <span className="text-[12px] font-bold max-w-[120px] truncate">
                  {userId}
                </span>
              </div>
              
              <button
                onClick={handleSignOut}
                className="text-[11px] font-bold text-[#c8cadf] hover:text-white transition-colors ml-1 flex items-center gap-1"
              >
                <LogOut className="w-3 h-3" />
                Logout
              </button>
            </div>
          )}

          {/* Session Management */}
          {userId && (
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-medium text-white/80 hidden lg:inline">Session:</span>
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
