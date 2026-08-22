"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Square } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StaffChatInputProps {
  onSubmit: (message: string) => void;
  onStop: () => void;
  isLoading: boolean;
  disabled?: boolean;
  isHero?: boolean;
  placeholder?: string;
}

export function StaffChatInput({
  onSubmit,
  onStop,
  isLoading,
  disabled = false,
  isHero = false,
  placeholder = "Ask anything about customer segments, deposit trends, card utilization, or loan portfolios...",
}: StaffChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading || disabled) return;

    onSubmit(input.trim());
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className={`w-full mx-auto transition-all ${
        isHero
          ? "max-w-3xl px-0"
          : "max-w-4xl px-4 pb-4 pt-2"
      }`}
    >
      <form
        onSubmit={handleSubmit}
        className={`relative flex flex-col bg-white dark:bg-slate-900 border transition-all overflow-hidden ${
          isHero
            ? "border-slate-300 dark:border-slate-700 focus-within:border-indigo-500 rounded-2xl shadow-lg shadow-slate-200/50 dark:shadow-2xl dark:shadow-black/60 focus-within:ring-4 focus-within:ring-indigo-500/10"
            : "border-slate-200 dark:border-slate-800 focus-within:border-indigo-500/60 rounded-2xl shadow-md dark:shadow-xl dark:shadow-black/40"
        }`}
      >
        {/* Text Area and Actions */}
        <div className={`flex items-end gap-2.5 ${isHero ? "p-3 sm:p-3.5" : "p-2.5 sm:p-3"}`}>
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className={`w-full resize-none bg-transparent border-0 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-0 max-h-44 py-1.5 leading-relaxed scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-800 ${
              isHero ? "text-sm sm:text-base min-h-[44px]" : "text-xs sm:text-sm min-h-[38px]"
            }`}
          />

          {/* Action button: Send or Stop */}
          <div className="shrink-0 flex items-center mb-0.5">
            {isLoading ? (
              <Button
                type="button"
                size="sm"
                variant="destructive"
                onClick={onStop}
                className={`p-0 rounded-xl bg-rose-600 hover:bg-rose-700 text-white shadow-md shadow-rose-900/30 transition-all ${
                  isHero ? "h-10 w-10" : "h-9 w-9"
                }`}
                title="Stop generation"
              >
                <Square className="h-4 w-4 fill-current" />
              </Button>
            ) : (
              <Button
                type="submit"
                size="sm"
                disabled={!input.trim() || disabled}
                className={`p-0 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-md shadow-indigo-600/30 disabled:opacity-40 disabled:pointer-events-none transition-all ${
                  isHero ? "h-10 w-10" : "h-9 w-9"
                }`}
                title="Send query"
              >
                <Send className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
