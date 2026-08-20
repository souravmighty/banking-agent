"use client";

import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card";
import {
  Loader2,
  Activity,
  Info,
  Search,
  Brain,
  ChevronDown,
  ChevronUp,
  Code,
  FileText,
  Database,
  Sparkles,
} from "lucide-react";
import ReactMarkdown, { Components } from "react-markdown";
import { mdComponents } from "@/components/chat/MarkdownRenderer";
import { ProcessedEvent } from "@/components/ActivityTimeline";

const darkTimelineMdComponents: Partial<Components> = {
  ...mdComponents,
  p: ({ children, ...props }) => (
    <p className="mb-1 leading-relaxed text-slate-700 dark:text-slate-300 last:mb-0 text-xs font-medium" {...props}>
      {children}
    </p>
  ),
  ul: ({ children, ...props }) => (
    <ul className="list-disc list-inside mb-1.5 space-y-0.5 text-slate-700 dark:text-slate-300 text-xs" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }) => (
    <ol className="list-decimal list-inside mb-1.5 space-y-0.5 text-slate-700 dark:text-slate-300 text-xs" {...props}>
      {children}
    </ol>
  ),
  li: ({ children, ...props }) => (
    <li className="leading-relaxed text-slate-700 dark:text-slate-300 text-xs" {...props}>
      {children}
    </li>
  ),
  code: ({ children, ...props }) => (
    <code className="bg-slate-100 dark:bg-slate-950 text-indigo-700 dark:text-indigo-300 px-1.5 py-0.5 rounded text-[11px] font-mono border border-slate-200 dark:border-slate-800" {...props}>
      {children}
    </code>
  ),
  a: ({ children, href, ...props }) => (
    <a className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300 underline transition-colors text-xs font-semibold" href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  ),
  strong: ({ children, ...props }) => (
    <strong className="font-bold text-slate-900 dark:text-white text-xs" {...props}>
      {children}
    </strong>
  ),
};

interface StaffActivityTimelineProps {
  processedEvents: ProcessedEvent[];
  isLoading: boolean;
}

export function StaffActivityTimeline({
  processedEvents,
  isLoading,
}: StaffActivityTimelineProps): React.JSX.Element {
  const [isTimelineCollapsed, setIsTimelineCollapsed] = useState<boolean>(false);

  const formatEventData = (data: unknown): string => {
    if (typeof data === "object" && data !== null && "type" in data) {
      const typedData = data as {
        type: string;
        content?: unknown;
        name?: string;
        args?: unknown;
        response?: unknown;
      };
      switch (typedData.type) {
        case "functionCall":
          return `Executing Tool: ${typedData.name}\nParameters:\n${JSON.stringify(
            typedData.args,
            null,
            2
          )}`;
        case "functionResponse":
          return `Tool [${typedData.name}] Output:\n${JSON.stringify(
            typedData.response,
            null,
            2
          )}`;
        case "text":
          return String(typedData.content || "");
        case "sources":
          const sources = typedData.content as Record<
            string,
            { title: string; url: string }
          >;
          if (Object.keys(sources).length === 0) {
            return "No references found.";
          }
          return Object.values(sources)
            .map(
              (source) =>
                `[${source.title || "Dataset View"}](${source.url})`
            )
            .join(", ");
        case "thinking":
          return String(typedData.content || "");
        default:
          return JSON.stringify(data, null, 2);
      }
    }

    if (typeof data === "string") {
      try {
        const parsed = JSON.parse(data);
        return JSON.stringify(parsed, null, 2);
      } catch {
        return data;
      }
    } else if (Array.isArray(data)) {
      return data.join(", ");
    } else if (typeof data === "object" && data !== null) {
      return JSON.stringify(data, null, 2);
    }
    return String(data);
  };

  const isJsonData = (data: unknown): boolean => {
    if (typeof data === "object" && data !== null && "type" in data) {
      const typedData = data as { type: string };
      if (typedData.type === "thinking" || typedData.type === "sources") {
        return false;
      }
      return (
        typedData.type === "functionCall" ||
        typedData.type === "functionResponse"
      );
    }

    if (typeof data === "string") {
      try {
        JSON.parse(data);
        return true;
      } catch {
        return false;
      }
    }
    return typeof data === "object" && data !== null;
  };

  const getEventIcon = (title: string) => {
    if (title.includes("BigQuery") || title.includes("SQL") || title.includes("database"))
      return <Database className="h-3.5 w-3.5" />;
    if (title.includes("Function Call") || title.includes("Calling"))
      return <Code className="h-3.5 w-3.5" />;
    if (title.includes("Function Response") || title.includes("Output"))
      return <FileText className="h-3.5 w-3.5" />;
    if (title.includes("Sources") || title.includes("Research"))
      return <Search className="h-3.5 w-3.5" />;
    if (title.includes("Planning") || title.includes("Hypothesis"))
      return <Brain className="h-3.5 w-3.5" />;
    if (title.includes("Processing") || title.includes("Analysis"))
      return <Activity className="h-3.5 w-3.5" />;
    if (title.includes("Thinking") || title.startsWith("🤔"))
      return <Sparkles className="h-3.5 w-3.5" />;
    return <Info className="h-3.5 w-3.5" />;
  };

  const getEventColor = (title: string): string => {
    if (title.includes("BigQuery") || title.includes("SQL")) return "text-cyan-600 dark:text-cyan-400";
    if (title.includes("Function Call")) return "text-blue-600 dark:text-blue-400";
    if (title.includes("Function Response")) return "text-emerald-600 dark:text-emerald-400";
    if (title.includes("Sources")) return "text-purple-600 dark:text-purple-400";
    if (title.includes("Planning") || title.includes("Hypothesis")) return "text-amber-600 dark:text-amber-400";
    if (title.includes("Thinking") || title.startsWith("🤔")) return "text-indigo-600 dark:text-indigo-400";
    return "text-slate-600 dark:text-slate-400";
  };

  const getEventBg = (title: string): string => {
    if (title.includes("BigQuery") || title.includes("SQL"))
      return "bg-cyan-50 dark:bg-cyan-950/30 border-cyan-200 dark:border-cyan-500/20";
    if (title.includes("Function Call")) return "bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-500/20";
    if (title.includes("Function Response")) return "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-500/20";
    if (title.includes("Sources")) return "bg-purple-50 dark:bg-purple-950/30 border-purple-200 dark:border-purple-500/20";
    if (title.includes("Planning") || title.includes("Hypothesis"))
      return "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-500/20";
    if (title.includes("Thinking") || title.startsWith("🤔"))
      return "bg-indigo-50 dark:bg-indigo-950/30 border-indigo-200 dark:border-indigo-500/20";
    return "bg-slate-50 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800";
  };

  return (
    <div className="w-full max-w-full mb-4 min-w-0">
      <Card className="bg-white dark:bg-slate-950/80 border-slate-200 dark:border-slate-800 shadow-sm dark:shadow-md rounded-xl overflow-hidden w-full max-w-full">
        <CardHeader className="py-2 px-3 sm:px-4 border-b border-slate-200 dark:border-slate-850 bg-slate-50 dark:bg-slate-900/40 w-full">
          <div className="flex items-center justify-between w-full min-w-0 gap-2">
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-50 dark:bg-indigo-600/20 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-500/30 shrink-0">
                <Activity className="h-3.5 w-3.5" />
              </div>
              <span className="text-slate-800 dark:text-slate-200 font-bold text-xs truncate">
                Analytics Execution Trace & Activity
              </span>
            </div>
            <button
              onClick={() => setIsTimelineCollapsed(!isTimelineCollapsed)}
              className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white shrink-0"
              aria-label={isTimelineCollapsed ? "Expand trace" : "Collapse trace"}
            >
              {isTimelineCollapsed ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronUp className="h-4 w-4" />
              )}
            </button>
          </div>
        </CardHeader>
        {!isTimelineCollapsed && (
          <CardContent className="pt-3 p-2.5 sm:p-4 w-full min-w-0">
            <div className="max-h-56 overflow-y-auto overflow-x-hidden w-full max-w-full pr-1 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-800 scrollbar-track-transparent">
              <div className="space-y-2.5 pr-1 w-full min-w-0">
                {processedEvents.map((event, index) => (
                  <div
                    key={index}
                    className={`flex items-start gap-2.5 p-2.5 rounded-lg border ${getEventBg(
                      event.title
                    )} transition-colors w-full min-w-0`}
                  >
                    <div
                      className={`mt-0.5 p-1 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 ${getEventColor(
                        event.title
                      )} shrink-0`}
                    >
                      {getEventIcon(event.title)}
                    </div>
                    <div className="flex-1 min-w-0 w-full">
                      <div
                        className={`text-[10px] sm:text-[11px] font-bold uppercase tracking-wider ${getEventColor(
                          event.title
                        )} truncate`}
                      >
                        {event.title}
                      </div>
                      <div className="text-xs mt-1 leading-relaxed w-full min-w-0">
                        {isJsonData(event.data) ? (
                          <pre className="whitespace-pre-wrap break-all font-mono text-[11px] bg-slate-900 dark:bg-slate-950/90 text-slate-100 dark:text-slate-300 p-2 sm:p-2.5 rounded-lg overflow-x-auto border border-slate-200 dark:border-slate-800 leading-normal w-full max-w-full">
                            {formatEventData(event.data)}
                          </pre>
                        ) : (
                          <div className="text-xs w-full min-w-0 break-words">
                            <ReactMarkdown components={darkTimelineMdComponents}>
                              {formatEventData(event.data)}
                            </ReactMarkdown>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex items-center gap-2 p-2.5 rounded-lg bg-indigo-50 dark:bg-slate-900/40 border border-indigo-200 dark:border-slate-800 animate-pulse w-full min-w-0">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-600 dark:text-indigo-400 shrink-0" />
                    <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-300 truncate">
                      Analytics Copilot is generating BigQuery query & hypothesis...
                    </span>
                  </div>
                )}
                {processedEvents.length === 0 && !isLoading && (
                  <div className="text-center py-4 text-slate-400 dark:text-slate-500 text-xs font-medium w-full">
                    Execution telemetry and tool calls will appear here in real time
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
