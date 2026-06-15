"use client";

import { BackendHealthChecker } from "@/components/chat/BackendHealthChecker";
import { ChatHeader } from "./ChatHeader";
import { ChatContent } from "./ChatContent";
import { ChatInput } from "./ChatInput";
import { useChatContext } from "./ChatProvider";
import { Loader2, Landmark } from "lucide-react";

/**
 * ChatLayout - Pure layout component for chat interface
 * Handles only UI structure and layout, no business logic
 * Uses context for all state management
 */
export function ChatContainer(): React.JSX.Element {
  const { isLoadingAuth, userId } = useChatContext();

  if (isLoadingAuth) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-[#1a1f71] text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-white text-[#1a1f71] flex items-center justify-center shadow-2xl animate-pulse">
            <Landmark className="h-8 w-8" />
          </div>
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-[#f0a500]" />
            <span className="text-sm font-medium tracking-wide">Authenticating Secure Connection...</span>
          </div>
        </div>
      </div>
    );
  }

  // If not loading and no user, we'll be redirected by useSession hook anyway
  if (!userId) return <></>;

  return (
    <div className="h-screen flex flex-col bg-[#f7f8fc] text-[#3a3f6e] relative overflow-hidden">
      <BackendHealthChecker>
        {/* Banking-themed background */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-[linear-gradient(180deg,#f7f8fc_0%,#f9fbff_100%)]"></div>
          <div className="absolute inset-x-0 top-0 h-px bg-[#d0d3ea]"></div>
        </div>

        {/* Fixed Header - stays at top */}
        <div className="relative z-10 flex-shrink-0">
          <ChatHeader />
        </div>

        {/* Scrollable Messages Area - takes remaining space */}
        <div className="relative z-10 flex-1 min-h-0">
          <ChatContent />
        </div>

        {/* Fixed Input Area - always at bottom */}
        <div className="relative z-10 flex-shrink-0">
          <ChatInput />
        </div>
      </BackendHealthChecker>
    </div>
  );
}
