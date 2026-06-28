import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import {
  Loader2,
  Activity,
  Info,
  Search,
  Brain,
  Pen,
  ChevronDown,
  ChevronUp,
  Code,
  FileText,
} from "lucide-react";
import { useState } from "react";
import ReactMarkdown, { Components } from "react-markdown";
import { mdComponents } from "@/components/chat/MarkdownRenderer";

const timelineMdComponents: Partial<Components> = {
  ...mdComponents,
  p: ({ children, ...props }) => (
    <p className="mb-1 leading-relaxed text-slate-600 last:mb-0 text-xs font-medium" {...props}>
      {children}
    </p>
  ),
  ul: ({ children, ...props }) => (
    <ul className="list-disc list-inside mb-1.5 space-y-0.5 text-slate-600 text-xs" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }) => (
    <ol className="list-decimal list-inside mb-1.5 space-y-0.5 text-slate-600 text-xs" {...props}>
      {children}
    </ol>
  ),
  li: ({ children, ...props }) => (
    <li className="leading-relaxed text-slate-600 text-xs" {...props}>
      {children}
    </li>
  ),
  code: ({ children, ...props }) => (
    <code className="bg-slate-100 text-[#1a1f71] px-1 py-0.5 rounded text-[11px] font-mono border border-slate-200/40" {...props}>
      {children}
    </code>
  ),
  a: ({ children, href, ...props }) => (
    <a className="text-[#1a1f71] hover:text-[#252b82] underline transition-colors text-xs font-semibold" href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  ),
  strong: ({ children, ...props }) => (
    <strong className="font-bold text-[#1a1f71] text-xs" {...props}>
      {children}
    </strong>
  ),
};

export interface ProcessedEvent {
  title: string;
  data: unknown;
}

interface ActivityTimelineProps {
  processedEvents: ProcessedEvent[];
  isLoading: boolean;
}

export function ActivityTimeline({
  processedEvents,
  isLoading,
}: ActivityTimelineProps): React.JSX.Element {
  const [isTimelineCollapsed, setIsTimelineCollapsed] =
    useState<boolean>(false);

  const formatEventData = (data: unknown): string => {
    // Handle structured data types for single agent
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
          return `Calling function: ${
            typedData.name
          }\nArguments: ${JSON.stringify(typedData.args, null, 2)}`;
        case "functionResponse":
          return `Function ${typedData.name} response:\n${JSON.stringify(
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
            return "No sources found.";
          }
          return Object.values(sources)
            .map(
              (source) =>
                `[${source.title || "Untitled Source"}](${source.url})`
            )
            .join(", ");
        case "thinking":
          return String(typedData.content || "");
        default:
          return JSON.stringify(data, null, 2);
      }
    }

    // Handle string data
    if (typeof data === "string") {
      // Try to parse as JSON first
      try {
        const parsed = JSON.parse(data);
        return JSON.stringify(parsed, null, 2);
      } catch {
        // If not JSON, return as string (could be markdown)
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
    // Handle structured data types
    if (typeof data === "object" && data !== null && "type" in data) {
      const typedData = data as { type: string };
      // Thinking and sources should use markdown rendering
      if (typedData.type === "thinking" || typedData.type === "sources") {
        return false; // Let ReactMarkdown handle this
      }
      // Only function calls and responses should use JSON rendering
      return (
        typedData.type === "functionCall" ||
        typedData.type === "functionResponse"
      );
    }

    // Check if string is JSON
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
    // Map different event types to icons for single agent
    if (title.includes("Function Call")) return <Code className="h-4 w-4" />;
    if (title.includes("Function Response"))
      return <FileText className="h-4 w-4" />;
    if (title.includes("Sources") || title.includes("Research"))
      return <Search className="h-4 w-4" />;
    if (title.includes("Planning") || title.includes("Strategy"))
      return <Brain className="h-4 w-4" />;
    if (title.includes("Processing") || title.includes("Analysis"))
      return <Activity className="h-4 w-4" />;
    if (title.includes("Writing") || title.includes("Report"))
      return <Pen className="h-4 w-4" />;
    if (title.includes("Thinking") || title.startsWith("🤔"))
      return <Brain className="h-4 w-4" />;
    return <Info className="h-4 w-4" />;
  };

  const getEventColor = (title: string): string => {
    // Color code different types of events
    if (title.includes("Function Call")) return "text-blue-600";
    if (title.includes("Function Response")) return "text-emerald-600";
    if (title.includes("Sources") || title.includes("Research"))
      return "text-purple-600";
    if (title.includes("Planning") || title.includes("Strategy"))
      return "text-amber-600";
    if (title.includes("Processing") || title.includes("Analysis"))
      return "text-orange-600";
    if (title.includes("Writing") || title.includes("Report"))
      return "text-rose-600";
    if (title.includes("Thinking") || title.startsWith("🤔"))
      return "text-indigo-600";
    return "text-slate-500";
  };

  const getEventBg = (title: string): string => {
    if (title.includes("Function Call")) return "bg-blue-50/40 border-blue-100/50";
    if (title.includes("Function Response")) return "bg-emerald-50/40 border-emerald-100/50";
    if (title.includes("Sources") || title.includes("Research")) return "bg-purple-50/40 border-purple-100/50";
    if (title.includes("Planning") || title.includes("Strategy")) return "bg-amber-50/40 border-amber-100/50";
    if (title.includes("Processing") || title.includes("Analysis")) return "bg-orange-50/40 border-orange-100/50";
    if (title.includes("Writing") || title.includes("Report")) return "bg-rose-50/40 border-rose-100/50";
    if (title.includes("Thinking") || title.startsWith("🤔")) return "bg-indigo-50/40 border-indigo-100/50";
    return "bg-slate-50/40 border-slate-100/50";
  };

  return (
    <div className="w-full max-w-full mb-4 min-w-0">
      <Card className="bg-white border-[#d0d3ea] shadow-sm rounded-2xl overflow-hidden w-full max-w-full">
        <CardHeader className="pb-3 border-b border-[#d0d3ea]/50 bg-[#f7f8fc]/80 w-full">
          <div className="flex items-center justify-between w-full min-w-0 gap-2">
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1a1f71]/5 text-[#1a1f71] ring-1 ring-[#1a1f71]/10 shrink-0">
                <Activity className="h-4 w-4" />
              </div>
              <CardDescription className="text-[#1a1f71] font-bold text-sm truncate">
                AI Activity Timeline
              </CardDescription>
            </div>
            <button
              onClick={() => setIsTimelineCollapsed(!isTimelineCollapsed)}
              className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors border border-transparent hover:border-slate-200 shrink-0"
            >
              {isTimelineCollapsed ? (
                <ChevronDown className="h-4 w-4 text-slate-500" />
              ) : (
                <ChevronUp className="h-4 w-4 text-slate-500" />
              )}
            </button>
          </div>
        </CardHeader>
        {!isTimelineCollapsed && (
          <CardContent className="pt-3 p-2 sm:p-4 w-full min-w-0">
            <div className="h-48 overflow-y-auto overflow-x-hidden w-full max-w-full pr-1 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
              <div className="space-y-3 pr-2 sm:pr-4 w-full min-w-0">
                {processedEvents.map((event, index) => (
                  <div
                    key={index}
                    className={`flex items-start gap-3 p-2.5 sm:p-3.5 rounded-xl border ${getEventBg(event.title)} shadow-sm hover:shadow transition-shadow w-full min-w-0`}
                  >
                    <div className={`mt-0.5 p-1.5 rounded-lg bg-white shadow-sm ring-1 ring-black/5 ${getEventColor(event.title)} shrink-0`}>
                      {getEventIcon(event.title)}
                    </div>
                    <div className="flex-1 min-w-0 w-full">
                      <div
                        className={`text-[10px] sm:text-xs font-bold uppercase tracking-wider ${getEventColor(
                          event.title
                        )} truncate`}
                      >
                        {event.title}
                      </div>
                      <div className="text-xs mt-1.5 leading-relaxed w-full min-w-0">
                        {isJsonData(event.data) ? (
                          <pre className="whitespace-pre-wrap break-all font-mono text-[11px] bg-slate-50 text-slate-800 p-2 sm:p-3 rounded-xl overflow-x-auto border border-slate-200/60 leading-normal w-full max-w-full">
                            {formatEventData(event.data)}
                          </pre>
                        ) : (
                          <div className="text-xs w-full min-w-0 break-words">
                            <ReactMarkdown components={timelineMdComponents}>
                              {formatEventData(event.data)}
                            </ReactMarkdown>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-slate-50 border border-slate-200/50 animate-pulse w-full min-w-0">
                    <Loader2 className="h-4 w-4 animate-spin text-[#1a1f71] shrink-0" />
                    <div className="text-xs font-bold text-[#1a1f71]/70 truncate">
                      AI is processing...
                    </div>
                  </div>
                )}
                {processedEvents.length === 0 && !isLoading && (
                  <div className="text-center py-8 text-slate-400 text-xs font-semibold w-full">
                    Activity will appear here as the AI processes your request
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
