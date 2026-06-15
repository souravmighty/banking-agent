"use client";

import { InputForm } from "@/components/InputForm";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * ChatInput - Input form wrapper with context integration
 * Handles message submission through context instead of prop drilling
 * Extracted from ChatMessagesView input section
 */
export function ChatInput(): React.JSX.Element {
  const { handleSubmit, isLoading, userId } = useChatContext();

  return (
    <div className="relative z-10 flex-shrink-0 border-t border-[#d0d3ea] bg-white/95 backdrop-blur-md shadow-sm">
      <div className="max-w-4xl mx-auto w-full p-4 pt-5">
        <InputForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          context="chat"
          userId={userId}
        />
      </div>
    </div>
  );
}
