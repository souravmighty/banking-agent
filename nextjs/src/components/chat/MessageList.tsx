"use client";

import { useState, useEffect } from "react";
import { MessageItem } from "./MessageItem";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Landmark, Loader2 } from "lucide-react";
import { Message } from "@/types";
import { ProcessedEvent } from "@/components/ActivityTimeline";

interface MessageListProps {
  messages: Message[];
  messageEvents?: Map<string, ProcessedEvent[]>;
  isLoading?: boolean;
  onCopy?: (text: string, messageId: string) => void;
  copiedMessageId?: string | null;
  scrollAreaRef?: React.RefObject<HTMLDivElement | null>;
}

/**
 * Message list component that efficiently renders all messages
 * with proper scrolling and performance optimization
 */
export function MessageList({
  messages,
  messageEvents,
  isLoading = false,
  onCopy,
  copiedMessageId,
  scrollAreaRef,
}: MessageListProps) {
  // If no messages, show empty state
  if (messages.length === 0) {
    return (
      <ScrollArea ref={scrollAreaRef} className="flex-1 px-4 py-6">
        <div className="flex items-center justify-center h-full">
          <div className="rounded-3xl border border-white/10 bg-white/6 px-6 py-5 text-center shadow-xl shadow-black/25 backdrop-blur-md">
            <div className="text-emerald-200 text-lg">💬</div>
            <p className="text-slate-200 text-sm mt-2">No messages yet. Start a secure conversation.</p>
          </div>
        </div>
      </ScrollArea>
    );
  }

  return (
    <ScrollArea ref={scrollAreaRef} className="flex-1 px-4 py-6">
      <div className="space-y-6 max-w-4xl mx-auto w-full">
        {messages.map((message, index) => (
          <MessageItem
            key={message.id}
            message={message}
            messageEvents={messageEvents}
            // Only show loading for the last message
            isLoading={isLoading && index === messages.length - 1}
            onCopy={onCopy}
            copiedMessageId={copiedMessageId}
          />
        ))}

        {/* Show "Planning..." if the last message is human and we are loading, and it is NOT the first message */}
        {isLoading &&
          messages.length > 1 &&
          messages[messages.length - 1].type === "human" && (
            <div className="flex items-start gap-3 max-w-[90%]">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#f0a500] text-[#1a1f71] flex items-center justify-center shadow-sm border border-[#f0a500]">
                <Landmark className="h-4 w-4" />
              </div>
              <div className="flex-1 rounded-3xl border border-[#d0d3ea] bg-white p-4 shadow-sm">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-[#f0a500]" />
                  <span className="text-sm text-[#3a3f6e]">
                    Preparing your banking response...
                  </span>
                </div>
              </div>
            </div>
          )}

        {/* Show Full-card Context Loader if it's the very first message query in the session */}
        {isLoading &&
          messages.length === 1 &&
          messages[0].type === "human" && (
            <ContextLoader />
          )}
      </div>
    </ScrollArea>
  );
}

/**
 * ContextLoader - Elegant step-by-step progress checklists
 * Keeps user informed during initial context generation and ADK sync (latency period)
 */
function ContextLoader(): React.JSX.Element {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStep((prev) => (prev < 3 ? prev + 1 : prev));
    }, 2200);
    return () => clearInterval(timer);
  }, []);

  const steps = [
    "Connecting to secure banking engine...",
    "Syncing customer profile context (secure verification protocols)...",
    "Loading ledger balances & risk metrics...",
    "Initializing conversational AI reasoning model...",
  ];

  return (
    <div className="mt-8 p-6 md:p-8 rounded-3xl border border-blue-900/10 bg-blue-50/40 backdrop-blur-sm shadow-md max-w-2xl mx-auto w-full flex flex-col items-center text-center animate-in fade-in duration-300">
      <div className="w-16 h-16 rounded-2xl bg-[#1a1f71] text-white flex items-center justify-center shadow-xl animate-bounce mb-6">
        <Landmark className="h-8 w-8" />
      </div>
      
      <h3 className="text-base font-extrabold text-[#1a1f71] tracking-tight">Syncing Secure Banking Context</h3>
      <p className="text-xs text-slate-500 mt-1.5 max-w-md leading-relaxed">
        We are compiling your secure portfolio and synchronizing customer credentials to enable personalized AI guidance. This occurs only on your first query of the session.
      </p>
      
      {/* Step List Card */}
      <div className="mt-6 w-full max-w-sm text-left space-y-3.5 bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        {steps.map((text, idx) => {
          const isDone = idx < step;
          const isActive = idx === step;
          const isPending = idx > step;

          return (
            <div key={idx} className="flex items-center gap-3 transition-opacity duration-300">
              {isDone && (
                <div className="flex-shrink-0 w-4 h-4 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-[9px] font-extrabold">
                  ✓
                </div>
              )}
              {isActive && (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-[#f0a500] flex-shrink-0" />
              )}
              {isPending && (
                <div className="h-1.5 w-1.5 rounded-full bg-slate-200 ml-1.5 mr-1 flex-shrink-0" />
              )}
              <span className={`text-xs font-semibold ${
                isDone 
                  ? "text-slate-400 line-through decoration-slate-200" 
                  : isActive 
                  ? "text-slate-700" 
                  : "text-slate-400"
              }`}>
                {text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
