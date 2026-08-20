import React from "react";
import { Sparkles } from "lucide-react";
import { StaffSessionSelector } from "./StaffSessionSelector";
import { ActiveSession } from "@/lib/actions/session-list-actions";

interface StaffChatHeaderProps {
  sessions: ActiveSession[];
  currentSessionId: string;
  onSessionSwitch: (sessionId: string) => void;
  onCreateNewSession: () => void;
  isLoading: boolean;
}

export function StaffChatHeader({
  sessions,
  currentSessionId,
  onSessionSwitch,
  onCreateNewSession,
  isLoading,
}: StaffChatHeaderProps) {
  return (
    <div className="border-b border-slate-200 dark:border-slate-800/80 bg-white/70 dark:bg-slate-950/40 px-4 sm:px-6 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 sticky top-0 z-10 backdrop-blur-sm transition-colors">
      {/* Left: Engine Details */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/20">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight">
              BankPilot Analytics Copilot
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
              BigQuery Agent
            </span>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Portfolio intelligence, diagnostic analytics & data exploration
          </p>
        </div>
      </div>

      {/* Right: Session Switcher */}
      <StaffSessionSelector
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSessionSwitch={onSessionSwitch}
        onCreateNewSession={onCreateNewSession}
        isLoading={isLoading}
      />
    </div>
  );
}
