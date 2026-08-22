"use client";

import React, { useState } from "react";
import { Message } from "@/types";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { StaffActivityTimeline } from "./StaffActivityTimeline";
import { StaffMarkdownRenderer } from "./StaffMarkdownRenderer";
import {
  Sparkles,
  User,
  Copy,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface StaffMessageItemProps {
  message: Message;
  timelineEvents?: ProcessedEvent[];
  isLoading?: boolean;
}

function getActiveTaskSummary(events: ProcessedEvent[]): string {
  if (!events || events.length === 0) {
    return "Formulating analytical plan & hypotheses...";
  }

  // Traverse from the latest event backward to find the current active operation
  for (let i = events.length - 1; i >= 0; i--) {
    const event = events[i];
    const data = event.data as Record<string, unknown> | undefined;
    if (!data) continue;

    if (data.type === "functionCall") {
      const name = typeof data.name === "string" ? data.name : "";
      const args = (data.args && typeof data.args === "object" ? data.args : {}) as Record<string, unknown>;

      if (name === "call_bigquery_agent" || name.includes("bigquery")) {
        const question = typeof args.question === "string" ? args.question : typeof args.request === "string" ? args.request : "";
        if (question.trim()) {
          const cleanQ = question.trim().replace(/^["']|["']$/g, "");
          return `Querying BigQuery: ${cleanQ.length > 85 ? cleanQ.slice(0, 82) + "..." : cleanQ}`;
        }
        return "Querying BigQuery analytical warehouse...";
      }

      if (name === "call_visualization_agent" || name.includes("visualization")) {
        const goal = typeof args.goal === "string" ? args.goal : "";
        if (goal.trim()) {
          const cleanGoal = goal.trim().replace(/^["']|["']$/g, "");
          return `Generating visualization: ${cleanGoal.length > 85 ? cleanGoal.slice(0, 82) + "..." : cleanGoal}`;
        }
        return "Generating interactive Vega-Lite visualization...";
      }

      if (name === "bigquery_nl2sql") {
        return "Translating business question into BigQuery SQL...";
      }

      if (name === "execute_sql") {
        return "Executing SQL query against analytical tables...";
      }

      if (name === "validate_vega_lite_spec") {
        return "Validating Vega-Lite chart specification...";
      }

      const formattedName = name.replace(/_/g, " ").trim();
      return `Executing ${formattedName || "analytical tool"}...`;
    }

    if (data.type === "functionResponse") {
      const name = typeof data.name === "string" ? data.name : "";
      if (name === "call_bigquery_agent") {
        return "Analyzing BigQuery records & calculating metrics...";
      }
      if (name === "call_visualization_agent") {
        return "Verifying visualization specification & rendering...";
      }
      return "Synthesizing retrieved analytics data...";
    }

    if (data.type === "thinking" || event.title.startsWith("🤔")) {
      const content = typeof data.content === "string" ? data.content.trim() : "";
      if (content) {
        const firstLine = content.split("\n")[0].trim();
        if (firstLine.length > 10) {
          return firstLine.length > 85 ? firstLine.slice(0, 82) + "..." : firstLine;
        }
      }
      return "Evaluating analytical hypotheses & data requirements...";
    }
  }

  return "Analyzing banking portfolio metrics & trends...";
}

export function StaffMessageItem({
  message,
  timelineEvents = [],
  isLoading = false,
}: StaffMessageItemProps) {
  const [copied, setCopied] = useState(false);
  const isAi = message.type === "ai";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy text");
    }
  };

  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  const activeTaskSummary = isAi && isLoading ? getActiveTaskSummary(timelineEvents) : "";

  return (
    <div
      className={`flex gap-3 sm:gap-4 py-4 px-2 sm:px-4 w-full transition-colors ${
        isAi
          ? "bg-slate-100/60 dark:bg-slate-950/40 border-y border-slate-200 dark:border-slate-900/60"
          : "bg-transparent"
      }`}
    >
      {/* Avatar */}
      <div className="shrink-0 mt-0.5">
        {isAi ? (
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 border border-indigo-400/30">
            <Sparkles className="h-4 w-4" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-xl bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-300 shadow-sm">
            <User className="h-4 w-4" />
          </div>
        )}
      </div>

      {/* Message Body */}
      <div className="flex-1 min-w-0 space-y-2">
        {/* Header: Author & Timestamp */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-900 dark:text-slate-200">
              {isAi ? "Analytics Copilot" : "Product & Business Lead"}
            </span>
            {isAi && (
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 font-semibold border border-indigo-200 dark:border-indigo-500/30">
                Executive AI
              </span>
            )}
            {formattedTime && (
              <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                {formattedTime}
              </span>
            )}
          </div>

          {/* Action buttons */}
          {isAi && message.content && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCopy}
              className="h-6 w-6 text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded"
              title="Copy message"
            >
              {copied ? (
                <Check className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          )}
        </div>

        {/* Activity Timeline (if AI and has events) */}
        {isAi && (timelineEvents.length > 0 || isLoading) && (
          <StaffActivityTimeline
            processedEvents={timelineEvents}
            isLoading={isLoading}
          />
        )}

        {/* Text Content */}
        {message.content ? (
          <div className="text-slate-800 dark:text-slate-100 text-xs sm:text-sm leading-relaxed overflow-hidden">
            <StaffMarkdownRenderer content={message.content} />
          </div>
        ) : isAi && isLoading ? (
          <div className="flex items-center gap-2 text-xs text-indigo-600 dark:text-indigo-400/90 font-medium py-1">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400 animate-pulse" />
            <span className="truncate">{activeTaskSummary}</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}
