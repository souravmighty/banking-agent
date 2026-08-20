"use client";

import React, { useEffect, useRef } from "react";
import { Message } from "@/types";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { StaffMessageItem } from "./StaffMessageItem";
import { StaffEmptyState } from "./StaffEmptyState";
import { Loader2 } from "lucide-react";

interface StaffMessageAreaProps {
  messages: Message[];
  messageEvents: Map<string, ProcessedEvent[]>;
  isLoading: boolean;
  isLoadingHistory: boolean;
  onSelectPrompt: (prompt: string) => void;
}

export function StaffMessageArea({
  messages,
  messageEvents,
  isLoading,
  isLoadingHistory,
  onSelectPrompt,
}: StaffMessageAreaProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  if (isLoadingHistory) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-500 dark:text-slate-400">
        <Loader2 className="h-6 w-6 animate-spin text-indigo-600 dark:text-indigo-400 mb-2" />
        <span className="text-xs font-semibold">Loading session analysis records...</span>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-800"
      >
        <StaffEmptyState onSelectPrompt={onSelectPrompt} />
      </div>
    );
  }

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-2 sm:px-6 py-4 space-y-1 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-800"
    >
      <div className="max-w-4xl mx-auto w-full divide-y divide-slate-200 dark:divide-slate-900/60">
        {messages.map((message, index) => {
          const events = messageEvents.get(message.id) || [];
          const isLast = index === messages.length - 1;
          const isCurrentLoading = isLast && isLoading && message.type === "ai";

          return (
            <StaffMessageItem
              key={message.id || index}
              message={message}
              timelineEvents={events}
              isLoading={isCurrentLoading}
            />
          );
        })}
      </div>
    </div>
  );
}
