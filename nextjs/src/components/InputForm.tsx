"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Send } from "lucide-react";

interface InputFormProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  context?: "homepage" | "chat";
}

export function InputForm({
  onSubmit,
  isLoading,
  context = "homepage",
}: InputFormProps): React.JSX.Element {
  const [inputValue, setInputValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current && context === "homepage") {
      textareaRef.current.focus();
    }
  }, [context]);

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSubmit(inputValue.trim());
      setInputValue("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const placeholderText =
    context === "chat"
      ? "Ask me anything about your account, payments, or banking..."
      : "How can I help you with your banking today?";

  return (
    <div className="w-full flex items-end gap-3">
      <form onSubmit={handleSubmit} className="flex-1">
        <div
          className={`
          relative flex items-end gap-3 p-2 rounded-2xl border transition-all duration-200
          ${
            isFocused
              ? "border-[#1a1f71] bg-white shadow-lg ring-2 ring-[#1a1f71]/5"
              : "border-[#d0d3ea] bg-white hover:border-[#1a1f71]/50 shadow-sm"
          }
        `}
        >
          {/* Input Area */}
          <div className="flex-1 px-2">
            <Textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={placeholderText}
              rows={1}
              className="
                resize-none border-0 bg-transparent text-[#1a1f71] placeholder-[#6b6f99]
                focus:ring-0 focus:outline-none focus:border-0 focus:shadow-none
                min-h-[44px] max-h-48
                scrollbar-thin scrollbar-track-transparent scrollbar-thumb-slate-300
                py-2.5 text-[15px]
              "
              style={{
                lineHeight: "1.5",
                border: "none",
                outline: "none",
                boxShadow: "none",
              }}
            />
          </div>

          {/* Send Button */}
          <Button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="
              h-11 px-6 rounded-xl bg-[#1a1f71] hover:bg-[#252b82]
              text-white border-0 shadow-sm transition-all duration-200
              disabled:opacity-40 disabled:bg-[#6b6f99]
              flex items-center gap-2 font-semibold
            "
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Send className="h-4 w-4" />
                <span className="hidden md:inline">Send</span>
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}

