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

  const isLandingState = messages.length === 0;

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

      {/* Messages Area / Landing View */}
      <StaffMessageArea
        messages={messages}
        messageEvents={messageEvents}
        isLoading={isLoading}
        isLoadingHistory={isLoadingHistory}
        onSelectPrompt={handleSubmit}
        inputComponent={
          isLandingState ? (
            <StaffChatInput
              onSubmit={handleSubmit}
              onStop={handleStopStream}
              isLoading={isLoading}
              disabled={isLoadingHistory || isInitializing}
              isHero={true}
            />
          ) : undefined
        }
      />

      {/* Chat Input Bar (only docked at bottom when active conversation is ongoing) */}
      {!isLandingState && (
        <StaffChatInput
          onSubmit={handleSubmit}
          onStop={handleStopStream}
          isLoading={isLoading}
          disabled={isLoadingHistory || isInitializing}
        />
      )}
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
