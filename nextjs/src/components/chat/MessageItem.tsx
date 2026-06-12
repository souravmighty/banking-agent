"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MarkdownRenderer, mdComponents } from "./MarkdownRenderer";
import {
  ActivityTimeline,
  ProcessedEvent,
} from "@/components/ActivityTimeline";
import { Copy, CopyCheck, Loader2, Bot, User } from "lucide-react";
import { Message } from "@/types";

interface MessageItemProps {
  message: Message;
  messageEvents?: Map<string, ProcessedEvent[]>;
  isLoading?: boolean;
  onCopy?: (text: string, messageId: string) => void;
  copiedMessageId?: string | null;
}

/**
 * Individual message component that handles both human and AI messages
 * with proper styling, copy functionality, and activity timeline
 */
export function MessageItem({
  message,
  messageEvents,
  isLoading = false,
  onCopy,
  copiedMessageId,
}: MessageItemProps) {
  const handleCopy = (text: string, messageId: string) => {
    if (onCopy) {
      onCopy(text, messageId);
    }
  };

  // Human message rendering
  if (message.type === "human") {
    return (
      <div className="flex items-start justify-end gap-3 max-w-[85%] ml-auto">
        <div className="bg-white text-[#1a1f71] p-4 rounded-3xl rounded-tr-sm shadow-sm border border-[#d0d3ea]">
          <ReactMarkdown
            components={{
              ...mdComponents,
              // Override styles for human messages (white text)
              p: ({ children, ...props }) => (
                <p
                  className="mb-2 leading-relaxed text-slate-900 last:mb-0"
                  {...props}
                >
                  {children}
                </p>
              ),
              h1: ({ children, ...props }) => (
                <h1
                  className="text-xl font-bold mb-3 text-slate-900 leading-tight"
                  {...props}
                >
                  {children}
                </h1>
              ),
              h2: ({ children, ...props }) => (
                <h2
                  className="text-lg font-semibold mb-2 text-slate-900 leading-tight"
                  {...props}
                >
                  {children}
                </h2>
              ),
              h3: ({ children, ...props }) => (
                <h3
                  className="text-base font-medium mb-2 text-slate-900 leading-tight"
                  {...props}
                >
                  {children}
                </h3>
              ),
              code: ({ children, ...props }) => (
                <code
                  className="bg-slate-200 text-slate-800 px-1.5 py-0.5 rounded text-sm font-mono"
                  {...props}
                >
                  {children}
                </code>
              ),
              strong: ({ children, ...props }) => (
                <strong className="font-semibold text-slate-900" {...props}>
                  {children}
                </strong>
              ),
            }}
            remarkPlugins={[remarkGfm]}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        <div className="flex-shrink-0 w-9 h-9 rounded-2xl bg-[#1a1f71] text-white flex items-center justify-center shadow-sm ring-1 ring-[#d0d3ea]">
          <User className="h-4 w-4" />
        </div>
      </div>
    );
  }

  // AI message rendering
  const hasTimelineEvents =
    messageEvents &&
    messageEvents.has(message.id) &&
    messageEvents.get(message.id)!.length > 0;

  // AI message loading with timeline events - show thinking indicator
  // Show this when loading AND we have timeline events (even if content started arriving)
  if (isLoading && hasTimelineEvents) {
    return (
      <div className="flex items-start gap-3 max-w-[90%]">
        <div className="flex-shrink-0 w-8 h-8 bg-[#1a1f71] rounded-full flex items-center justify-center shadow-sm border border-[#d0d3ea]">
          <Bot className="h-4 w-4 text-white" />
        </div>

        <div className="flex-1 rounded-2xl rounded-tl-sm border border-[#d0d3ea] bg-white p-4 shadow-sm">
          {/* Activity Timeline during thinking */}
          {hasTimelineEvents && (
            <ActivityTimeline
              processedEvents={messageEvents.get(message.id) || []}
              isLoading={isLoading}
            />
          )}

          {/* Show content if it exists while loading */}
          {message.content && (
            <div className="prose prose-invert max-w-none mb-3">
              <MarkdownRenderer content={message.content} />
            </div>
          )}

          {/* Loading indicator */}
          <div className="flex items-center gap-2 rounded-lg border border-[#d0d3ea] bg-[#f5f7ff] px-3 py-2">
            <Loader2 className="h-4 w-4 animate-spin text-[#1a1f71]" />
            <span className="text-sm text-[#5a6197]">
              {message.content
                ? "🚀 Still processing..."
                : "🤔 Thinking and planning..."}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // AI message with no content and not loading - show timeline if available
  if (!message.content) {
    // If we have timeline events, show them even without content
    if (hasTimelineEvents) {
      return (
        <div className="flex items-start gap-3 max-w-[90%]">
          <div className="flex-shrink-0 w-8 h-8 bg-[#1a1f71] rounded-full flex items-center justify-center shadow-sm border border-[#d0d3ea]">
            <Bot className="h-4 w-4 text-white" />
          </div>

          <div className="flex-1 rounded-3xl border border-[#d0d3ea] bg-white p-4 shadow-sm">
            <ActivityTimeline
              processedEvents={messageEvents.get(message.id) || []}
              isLoading={isLoading}
            />

            {/* Show thinking indicator */}
            <div className="mt-3 flex items-center gap-2 rounded-2xl border border-[#d0d3ea] bg-[#f5f7ff] px-3 py-2">
              <span className="text-sm text-[#1a1f71]">🤔 Thinking...</span>
            </div>
          </div>
        </div>
      );
    }

    // Otherwise show no content indicator
    return (
      <div className="flex items-start gap-3 max-w-[90%]">
        <div className="flex-shrink-0 w-8 h-8 bg-[#1a1f71] rounded-full flex items-center justify-center shadow-sm border border-[#d0d3ea]">
          <Bot className="h-4 w-4 text-white" />
        </div>
        <div className="flex items-center gap-2 rounded-2xl border border-[#d0d3ea] bg-white px-3 py-2 shadow-sm">
          <span className="text-sm text-[#5a6197]">No content</span>
        </div>
      </div>
    );
  }

  // Regular AI message display with content
  return (
    <div className="flex items-start gap-3 max-w-[90%]">
      <div className="flex-shrink-0 w-8 h-8 bg-[#1a1f71] rounded-full flex items-center justify-center shadow-sm border border-[#d0d3ea]">
        <Bot className="h-4 w-4 text-white" />
      </div>

      <div className="flex-1 rounded-3xl border border-[#d0d3ea] bg-white p-4 shadow-sm relative group">
        {/* Activity Timeline */}
        {messageEvents && messageEvents.has(message.id) && (
          <ActivityTimeline
            processedEvents={messageEvents.get(message.id) || []}
            isLoading={isLoading}
          />
        )}

        {/* Message content */}
        <div className="prose prose-invert max-w-none">
          <MarkdownRenderer content={message.content} />
        </div>

        {/* Copy button */}
        {onCopy && (
          <button
            onClick={() => handleCopy(message.content, message.id)}
            className="absolute top-3 right-3 p-2 rounded-xl border border-[#d0d3ea] bg-[#f5f7ff] hover:bg-[#edf1ff] transition-colors opacity-0 group-hover:opacity-100"
            title="Copy message"
          >
            {copiedMessageId === message.id ? (
              <CopyCheck className="h-4 w-4 text-[#1a1f71]" />
            ) : (
              <Copy className="h-4 w-4 text-[#5a6197] hover:text-[#1a1f71]" />
            )}
          </button>
        )}

        {/* Timestamp */}
        <div className="mt-3 pt-2 border-t border-white/8">
          <span className="text-xs text-[#5a6197]">
            {message.timestamp.toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
}
