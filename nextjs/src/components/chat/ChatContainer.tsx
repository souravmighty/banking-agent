"use client";

import { BackendHealthChecker } from "@/components/chat/BackendHealthChecker";
import { ChatHeader } from "./ChatHeader";
import { ChatContent } from "./ChatContent";
import { ChatInput } from "./ChatInput";

/**
 * ChatLayout - Pure layout component for chat interface
 * Handles only UI structure and layout, no business logic
 * Uses context for all state management
 */
export function ChatContainer(): React.JSX.Element {
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
