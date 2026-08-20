"use client";

import React from "react";
import { StaffChatProvider, useStaffChat } from "./StaffChatProvider";
import { StaffChatHeader } from "./StaffChatHeader";
import { StaffMessageArea } from "./StaffMessageArea";
import { StaffChatInput } from "./StaffChatInput";

function StaffChatInner() {
  const {
    messages,
    messageEvents,
    sessions,
    currentSessionId,
    isLoading,
    isLoadingHistory,
    isInitializing,
    handleSubmit,
    handleStopStream,
    handleSessionSwitch,
    handleCreateNewSession,
  } = useStaffChat();

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-4rem)] max-h-[calc(100vh-4rem)] overflow-hidden bg-slate-50 dark:bg-[#060814] text-slate-900 dark:text-slate-100 transition-colors">
      {/* Analytics Chat Header */}
      <StaffChatHeader
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSessionSwitch={handleSessionSwitch}
        onCreateNewSession={handleCreateNewSession}
        isLoading={isInitializing}
      />

      {/* Messages / Conversation Area */}
      <StaffMessageArea
        messages={messages}
        messageEvents={messageEvents}
        isLoading={isLoading}
        isLoadingHistory={isLoadingHistory}
        onSelectPrompt={handleSubmit}
      />

      {/* Chat Input Bar */}
      <StaffChatInput
        onSubmit={handleSubmit}
        onStop={handleStopStream}
        isLoading={isLoading}
        disabled={isLoadingHistory || isInitializing}
      />
    </div>
  );
}

export function StaffChatContainer() {
  return (
    <StaffChatProvider>
      <StaffChatInner />
    </StaffChatProvider>
  );
}
