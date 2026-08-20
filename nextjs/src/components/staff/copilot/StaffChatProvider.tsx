"use client";

import React, {
  createContext,
  useContext,
  useState,
  useRef,
  useCallback,
  useEffect,
} from "react";
import { Message } from "@/types";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { useAuth } from "@/hooks/useAuth";
import { useStreaming } from "@/hooks/useStreaming";
import { createSessionAction } from "@/lib/actions/session-actions";
import {
  fetchActiveSessionsAction,
  ActiveSession,
} from "@/lib/actions/session-list-actions";
import { loadSessionHistoryAction } from "@/lib/actions/session-history-actions";
import { toast } from "sonner";

export interface StaffChatContextValue {
  messages: Message[];
  messageEvents: Map<string, ProcessedEvent[]>;
  sessions: ActiveSession[];
  currentSessionId: string;
  isLoading: boolean;
  isLoadingHistory: boolean;
  isInitializing: boolean;
  currentAgent: string;
  handleSubmit: (query: string) => Promise<void>;
  handleStopStream: () => void;
  handleSessionSwitch: (sessionId: string) => void;
  handleCreateNewSession: () => Promise<void>;
  scrollAreaRef: React.RefObject<HTMLDivElement | null>;
}

const StaffChatContext = createContext<StaffChatContextValue | null>(null);

const APP_NAME = "analytics_copilot_2";

export function StaffChatProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const userId = user?.uid || user?.email || "staff_admin";

  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageEvents, setMessageEvents] = useState<Map<string, ProcessedEvent[]>>(
    new Map()
  );

  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const newlyCreatedSessionIdRef = useRef<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement | null>(null);

  // Streaming Hook
  const { isLoading, currentAgent, startStream, stopStream } = useStreaming(
    async (fn) => fn()
  );

  // Fetch active sessions list
  const refreshSessions = useCallback(async () => {
    if (!userId) return;
    try {
      const result = await fetchActiveSessionsAction(userId, APP_NAME);
      if (result.success && result.sessions) {
        setSessions(result.sessions);
        if (result.sessions.length > 0 && !currentSessionId) {
          // Default to most recent session
          setCurrentSessionId(result.sessions[0].id);
        }
      }
    } catch (err) {
      console.warn("Error loading staff active sessions:", err);
    }
  }, [userId, currentSessionId]);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  // Load session history when currentSessionId changes
  useEffect(() => {
    if (!userId || !currentSessionId) return;

    if (newlyCreatedSessionIdRef.current === currentSessionId) {
      return;
    }

    const loadHistory = async () => {
      try {
        setIsLoadingHistory(true);
        setMessages([]);
        setMessageEvents(new Map());

        const result = await loadSessionHistoryAction(
          userId,
          currentSessionId,
          APP_NAME
        );

        if (result.success) {
          if (result.messages && result.messages.length > 0) {
            setMessages(result.messages);
          }
          if (result.messageEvents && result.messageEvents.size > 0) {
            setMessageEvents(result.messageEvents);
          }
        }
      } catch (error) {
        console.error("Error loading staff session history:", error);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadHistory();
  }, [userId, currentSessionId]);

  // Create new session
  const handleCreateNewSession = useCallback(async () => {
    if (!userId) {
      toast.error("Please sign in to start a session");
      return;
    }

    try {
      setIsInitializing(true);
      const toastId = toast.loading("Initializing Analytics Copilot session...");

      const result = await createSessionAction(userId, APP_NAME);

      if (result.success && result.sessionId) {
        newlyCreatedSessionIdRef.current = result.sessionId;
        setMessages([]);
        setMessageEvents(new Map());
        setCurrentSessionId(result.sessionId);
        toast.success("New investigation session created", { id: toastId });
        await refreshSessions();
      } else {
        toast.error("Failed to create analytics session", { id: toastId });
      }
    } catch (error) {
      console.error("Error creating staff session:", error);
      toast.error("Failed to initialize session");
    } finally {
      setIsInitializing(false);
    }
  }, [userId, refreshSessions]);

  // Switch session
  const handleSessionSwitch = useCallback((sessionId: string) => {
    if (sessionId === currentSessionId) return;
    newlyCreatedSessionIdRef.current = null;
    setCurrentSessionId(sessionId);
  }, [currentSessionId]);

  // Submit message
  const handleSubmit = useCallback(
    async (query: string): Promise<void> => {
      if (!query.trim() || !userId) return;

      try {
        let activeSessionId = currentSessionId;

        // Auto-create session if none active
        if (!activeSessionId) {
          setIsInitializing(true);
          const result = await createSessionAction(userId, APP_NAME);
          if (result.success && result.sessionId) {
            activeSessionId = result.sessionId;
            newlyCreatedSessionIdRef.current = activeSessionId;
            setCurrentSessionId(activeSessionId);
          } else {
            // Generate temporary local ID if server create fails
            activeSessionId = `session-${Date.now()}`;
            setCurrentSessionId(activeSessionId);
          }
          setIsInitializing(false);
        }

        // Add human message to chat
        const userMessage: Message = {
          type: "human",
          content: query,
          id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);

        // Streaming update callbacks
        const handleMessageUpdate = (updatedMsg: Message) => {
          setMessages((prev) => {
            const exists = prev.find((m) => m.id === updatedMsg.id);
            if (exists) {
              return prev.map((m) =>
                m.id === updatedMsg.id ? { ...exists, ...updatedMsg } : m
              );
            } else {
              return [...prev, updatedMsg];
            }
          });
        };

        const handleEventUpdate = (messageId: string, event: ProcessedEvent) => {
          setMessageEvents((prev) => {
            const nextMap = new Map(prev);
            const events = nextMap.get(messageId) || [];

            if (event.title.startsWith("🤔")) {
              const idx = events.findIndex((e) => e.title === event.title);
              if (idx >= 0) {
                const nextEvents = [...events];
                nextEvents[idx] = event;
                nextMap.set(messageId, nextEvents);
              } else {
                nextMap.set(messageId, [...events, event]);
              }
            } else {
              nextMap.set(messageId, [...events, event]);
            }
            return nextMap;
          });
        };

        await startStream(
          {
            message: query,
            userId,
            sessionId: activeSessionId,
            appName: APP_NAME,
          },
          handleMessageUpdate,
          handleEventUpdate,
          () => {}
        );

        // Refresh session list to update counts
        refreshSessions();
      } catch (error) {
        console.error("Error submitting query to Analytics Copilot:", error);
        toast.error("Query Execution Notice", {
          description:
            error instanceof Error
              ? error.message
              : "Unable to reach Analytics Copilot engine. Please check backend status.",
        });
      }
    },
    [userId, currentSessionId, startStream, refreshSessions]
  );

  const handleStopStream = useCallback(() => {
    stopStream();
  }, [stopStream]);

  const value: StaffChatContextValue = {
    messages,
    messageEvents,
    sessions,
    currentSessionId,
    isLoading,
    isLoadingHistory,
    isInitializing,
    currentAgent,
    handleSubmit,
    handleStopStream,
    handleSessionSwitch,
    handleCreateNewSession,
    scrollAreaRef,
  };

  return (
    <StaffChatContext.Provider value={value}>
      {children}
    </StaffChatContext.Provider>
  );
}

export function useStaffChat(): StaffChatContextValue {
  const context = useContext(StaffChatContext);
  if (!context) {
    throw new Error("useStaffChat must be used within StaffChatProvider");
  }
  return context;
}
