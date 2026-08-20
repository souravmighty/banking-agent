import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Plus, History, Loader2 } from "lucide-react";
import { ActiveSession } from "@/lib/actions/session-list-actions";

interface StaffSessionSelectorProps {
  sessions: ActiveSession[];
  currentSessionId: string;
  onSessionSwitch: (sessionId: string) => void;
  onCreateNewSession: () => void;
  isLoading?: boolean;
}

export function StaffSessionSelector({
  sessions,
  currentSessionId,
  onSessionSwitch,
  onCreateNewSession,
  isLoading = false,
}: StaffSessionSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="relative min-w-[200px] max-w-[280px]">
        <Select
          value={currentSessionId}
          onValueChange={(val) => onSessionSwitch(val)}
        >
          <SelectTrigger className="h-9 bg-white dark:bg-slate-900/90 border-slate-200 dark:border-slate-800 text-xs text-slate-800 dark:text-slate-200 focus:ring-1 focus:ring-indigo-500 rounded-xl shadow-sm">
            <div className="flex items-center gap-2 truncate">
              <History className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400 shrink-0" />
              <SelectValue placeholder="Select Investigation Session" />
            </div>
          </SelectTrigger>
          <SelectContent className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-xl shadow-2xl">
            {sessions.length === 0 ? (
              <div className="px-3 py-2 text-xs text-slate-400 dark:text-slate-500 text-center">
                No active sessions
              </div>
            ) : (
              sessions.map((session) => (
                <SelectItem
                  key={session.id}
                  value={session.id}
                  className="text-xs hover:bg-slate-100 dark:hover:bg-slate-800 focus:bg-slate-100 dark:focus:bg-slate-800 focus:text-slate-900 dark:focus:text-white cursor-pointer py-2"
                >
                  <div className="flex flex-col text-left">
                    <span className="font-semibold text-slate-900 dark:text-slate-200">
                      {session.title || `Session ${session.id.substring(0, 8)}`}
                    </span>
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                      {session.messageCount} messages ·{" "}
                      {session.lastUpdateTime
                        ? new Date(session.lastUpdateTime).toLocaleDateString([], {
                            month: "short",
                            day: "numeric",
                          })
                        : "Recent"}
                    </span>
                  </div>
                </SelectItem>
              ))
            )}
          </SelectContent>
        </Select>
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={onCreateNewSession}
        disabled={isLoading}
        className="h-9 px-3 text-xs font-semibold bg-white dark:bg-slate-900/90 border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white text-slate-700 dark:text-slate-300 rounded-xl gap-1.5 shrink-0 shadow-sm transition-colors"
      >
        {isLoading ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-600 dark:text-indigo-400" />
        ) : (
          <Plus className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
        )}
        <span className="hidden sm:inline">New Analysis</span>
      </Button>
    </div>
  );
}
