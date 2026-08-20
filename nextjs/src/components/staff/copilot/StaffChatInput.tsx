import React, { useState, useRef, useEffect } from "react";
import { Send, Square, Database } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StaffChatInputProps {
  onSubmit: (message: string) => void;
  onStop: () => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function StaffChatInput({
  onSubmit,
  onStop,
  isLoading,
  disabled = false,
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
    <div className="w-full max-w-4xl mx-auto px-4 pb-4 pt-2">
      <form
        onSubmit={handleSubmit}
        className="relative flex flex-col bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 focus-within:border-indigo-500/60 rounded-2xl shadow-lg dark:shadow-xl dark:shadow-black/40 transition-all overflow-hidden"
      >
        {/* Top input bar with hints */}
        <div className="flex items-center justify-between px-4 pt-2.5 text-[10px] text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-100 dark:border-slate-850/60 select-none">
          <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400">
            <Database className="h-3 w-3" />
            <span>BigQuery NL2SQL & Portfolio Models</span>
          </div>
          <span className="hidden sm:inline text-slate-400 dark:text-slate-500">
            Press <kbd className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono text-[9px]">Enter ↵</kbd> to execute
          </span>
        </div>

        {/* Text Area */}
        <div className="flex items-end gap-2 p-3">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Analytics Copilot about customer portfolios, transaction metrics, demo pools, or SQL queries..."
            disabled={disabled}
            className="w-full resize-none bg-transparent border-0 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 text-xs sm:text-sm focus:outline-none focus:ring-0 max-h-44 min-h-[36px] py-1.5 leading-relaxed scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-800"
          />

          {/* Action button: Send or Stop */}
          <div className="shrink-0 flex items-center gap-1">
            {isLoading ? (
              <Button
                type="button"
                size="sm"
                variant="destructive"
                onClick={onStop}
                className="h-9 w-9 p-0 rounded-xl bg-rose-600 hover:bg-rose-700 text-white shadow-md shadow-rose-900/30"
                title="Stop generation"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
              </Button>
            ) : (
              <Button
                type="submit"
                size="sm"
                disabled={!input.trim() || disabled}
                className="h-9 w-9 p-0 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-md shadow-indigo-600/30 disabled:opacity-40 disabled:pointer-events-none transition-all"
                title="Send query"
              >
                <Send className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </form>

      {/* Safety & Compliance disclaimer */}
      <div className="text-center mt-2 text-[10px] text-slate-500 dark:text-slate-400">
        BankPilot Analytics Copilot accesses aggregated operational databases. Verify mission-critical financial calculations.
      </div>
    </div>
  );
}
