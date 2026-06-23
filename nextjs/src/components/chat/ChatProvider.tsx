"use client";

import React, {
  createContext,
  useContext,
  useRef,
  useCallback,
  useEffect,
  useState,
} from "react";

import { useSession } from "@/hooks/useSession";
import { useMessages } from "@/hooks/useMessages";
import { useStreamingManager } from "@/components/chat/StreamingManager";
import { Message } from "@/types";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { toast } from "sonner";
import { loadSessionHistoryAction } from "@/lib/actions/session-history-actions";
import { fetchActiveSessionsAction } from "@/lib/actions/session-list-actions";

// Context value interface - consolidates all chat state and actions
export interface ChatContextValue {
  // Session state
  userId: string;
  userEmail: string;
  sessionId: string;
  isFirstSession: boolean;

  // Message state
  messages: Message[];
  messageEvents: Map<string, ProcessedEvent[]>;
  websiteCount: number;

  // Loading state
  isLoading: boolean;
  isLoadingHistory: boolean; // New loading state for session history
  isLoadingAuth: boolean;
  isInitializing: boolean; // Loading state for new session auto-creation
  currentAgent: string;

  // Session actions
  handleCreateNewSession: (sessionUserId: string) => Promise<void>;
  handleSessionSwitch: (newSessionId: string) => void;
  handleSignOut: () => Promise<void>;

  // Message actions
  handleSubmit: (
    query: string,
    requestUserId?: string,
    requestSessionId?: string
  ) => Promise<void>;
  handleStopStream: () => void;
  addMessage: (message: Message) => void;

  // Refs for external access
  scrollAreaRef: React.RefObject<HTMLDivElement | null>;
}

interface ChatProviderProps {
  children: React.ReactNode;
}

// Create context
const ChatContext = createContext<ChatContextValue | null>(null);

/**
 * ChatProvider - Consolidated context provider for all chat state management
 * Combines useSession, useMessages, and useStreamingManager into single provider
 */
export function ChatProvider({
  children,
}: ChatProviderProps): React.JSX.Element {
  const scrollAreaRef = useRef<HTMLDivElement | null>(null);
  const newlyCreatedSessionIdRef = useRef<string | null>(null);

  // Session history loading state
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const [isFirstSession, setIsFirstSession] = useState<boolean>(false);

  // Consolidate all hooks
  const {
    userId,
    userEmail,
    sessionId,
    isLoadingAuth,
    handleSessionSwitch,
    handleSignOut,
  } = useSession();

  // Check if it's the user's first ever session
  useEffect(() => {
    if (userId) {
      fetchActiveSessionsAction(userId)
        .then((result) => {
          if (result.success) {
            setIsFirstSession(result.sessions.length <= 1);
          } else {
            setIsFirstSession(true);
          }
        })
        .catch((err) => {
          console.error("Error checking sessions in provider:", err);
          setIsFirstSession(true);
        });
    }
  }, [userId]);

  const {
    messages,
    messageEvents,
    websiteCount,
    addMessage,
    setMessages,
    setMessageEvents,
    updateWebsiteCount,
  } = useMessages();

  // Custom handleCreateNewSession wrapper to intercept manual new session creation
  const handleCreateNewSession = useCallback(
    async (sessionUserId: string): Promise<void> => {
      try {
        setIsInitializing(true);
        const { createSessionAction } = await import(
          "@/lib/actions/session-actions"
        );
        const result = await createSessionAction(sessionUserId);
        
        if (result.success && result.sessionId) {
          newlyCreatedSessionIdRef.current = result.sessionId;
          // Pre-emptively clear messages and events to avoid flashing previous session content
          setMessages([]);
          setMessageEvents(new Map());
          updateWebsiteCount(0);
          handleSessionSwitch(result.sessionId);
        } else {
          throw new Error(result.error || "Failed to create session");
        }
      } catch (error) {
        console.error("Error creating new session:", error);
        toast.error("Failed to create session");
      } finally {
        setIsInitializing(false);
      }
    },
    [handleSessionSwitch, setMessages, setMessageEvents, updateWebsiteCount]
  );

  // Streaming management
  const streamingManager = useStreamingManager({
    userId,
    sessionId,
    onMessageUpdate: (message: Message) => {
      console.log("🔄 [CHAT_PROVIDER] onMessageUpdate called:", {
        messageId: message.id,
        messageType: message.type,
        contentLength: message.content.length,
        hasContent: !!message.content,
      });

      setMessages((prev) => {
        const existingMessage = prev.find((msg) => msg.id === message.id);
        console.log("🔍 [CHAT_PROVIDER] Message state check:", {
          messageId: message.id,
          existingMessage: !!existingMessage,
          totalMessages: prev.length,
          lastMessageType:
            prev.length > 0 ? prev[prev.length - 1].type : "none",
        });

        if (existingMessage) {
          // Update existing message while preserving any additional data
          console.log("🔄 [CHAT_PROVIDER] Updating existing message");
          return prev.map((msg) =>
            msg.id === message.id
              ? {
                  ...existingMessage, // Keep existing data
                  ...message, // Update with new content
                }
              : msg
          );
        } else {
          // Create new message with proper initial state
          const newMessage: Message = {
            ...message,
            timestamp: message.timestamp || new Date(),
          };
          console.log("✅ [CHAT_PROVIDER] Creating new message:", {
            id: newMessage.id,
            type: newMessage.type,
            contentLength: newMessage.content.length,
          });
          const newMessages = [...prev, newMessage];
          console.log("📊 [CHAT_PROVIDER] Updated messages array:", {
            totalMessages: newMessages.length,
            lastMessageType: newMessages[newMessages.length - 1].type,
          });
          return newMessages;
        }
      });
    },
    onEventUpdate: (messageId, event) => {
      console.log("📅 [CHAT_PROVIDER] onEventUpdate called:", {
        messageId,
        eventTitle: event.title,
        eventType:
          typeof event.data === "object" && event.data && "type" in event.data
            ? event.data.type
            : undefined,
        isThought: event.title.startsWith("🤔"),
      });

      setMessageEvents((prev) => {
        const newMap = new Map(prev);
        const existingEvents = newMap.get(messageId) || [];
        console.log("🔍 [CHAT_PROVIDER] Event state check:", {
          messageId,
          existingEventsCount: existingEvents.length,
          eventTitle: event.title,
        });

        // Handle thinking activities with progressive content accumulation
        if (event.title.startsWith("🤔")) {
          const existingThinkingIndex = existingEvents.findIndex(
            (existingEvent) => existingEvent.title === event.title
          );

          if (existingThinkingIndex >= 0) {
            // Accumulate content progressively instead of replacing
            const updatedEvents = [...existingEvents];
            const existingEvent = updatedEvents[existingThinkingIndex];
            const existingData =
              existingEvent.data && typeof existingEvent.data === "object"
                ? existingEvent.data
                : {};
            const existingContent =
              "content" in existingData ? String(existingData.content) : "";
            const newContent =
              event.data &&
              typeof event.data === "object" &&
              "content" in event.data
                ? String(event.data.content)
                : "";

            // Accumulate content (don't replace - add new content)
            const accumulatedContent = existingContent
              ? `${existingContent}\n\n${newContent}`
              : newContent;

            updatedEvents[existingThinkingIndex] = {
              ...existingEvent,
              data: {
                ...existingData,
                content: accumulatedContent,
              },
            };
            newMap.set(messageId, updatedEvents);
          } else {
            // Add new thinking activity (each distinct thought title)
            newMap.set(messageId, [...existingEvents, event]);
          }
        } else {
          // For non-thinking activities, add normally (no deduplication needed)
          newMap.set(messageId, [...existingEvents, event]);
        }

        return newMap;
      });
    },
    onWebsiteCountUpdate: updateWebsiteCount,
  });

  // Load session history when session changes
  useEffect(() => {
    if (userId && sessionId) {
      if (newlyCreatedSessionIdRef.current === sessionId) {
        console.log("⏭️ [CHAT_PROVIDER] Skipping history load for newly created session:", sessionId);
        newlyCreatedSessionIdRef.current = null;
        return;
      }

      // Function to load session history
      const loadSessionHistory = async () => {
        try {
          console.log("🔄 [CHAT_PROVIDER] Loading session history:", {
            userId,
            sessionId,
          });

          setIsLoadingHistory(true);

          // Clear current state
          setMessages([]);
          setMessageEvents(new Map());
          updateWebsiteCount(0);

          // Load session history using Server Action (keeps Google Auth on server)
          const result = await loadSessionHistoryAction(userId, sessionId);

          if (result.success) {
            console.log(
              "✅ [CHAT_PROVIDER] Session history loaded successfully:",
              {
                messagesCount: result.messages.length,
                eventsCount: result.messageEvents.size,
              }
            );

            // Set historical messages
            if (result.messages.length > 0) {
              setMessages(result.messages);
            }

            // Set timeline events
            if (result.messageEvents.size > 0) {
              setMessageEvents(result.messageEvents);
            }

            console.log("✅ [CHAT_PROVIDER] Session history applied to state");
          } else {
            console.warn(
              "⚠️ [CHAT_PROVIDER] Session history loading failed:",
              result.error
            );

            // Show error toast to user
            toast.error("Failed to load chat history", {
              description:
                result.error ||
                "Could not load previous messages for this session.",
            });
          }
        } catch (error) {
          console.error(
            "❌ [CHAT_PROVIDER] Error loading session history:",
            error
          );

          // Show error toast to user
          toast.error("Network error", {
            description:
              "Could not connect to load chat history. Please check your connection.",
          });

          // On error, just clear state and continue (graceful degradation)
          setMessages([]);
          setMessageEvents(new Map());
          updateWebsiteCount(0);
        } finally {
          setIsLoadingHistory(false);
        }
      };

      // Load session history
      loadSessionHistory();
    }
  }, [userId, sessionId, setMessages, setMessageEvents, updateWebsiteCount]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [messages]);

  // Handle message submission
  const handleSubmit = useCallback(
    async (
      query: string,
      requestUserId?: string,
      requestSessionId?: string
    ): Promise<void> => {
      if (!query.trim()) return;

      // Use provided userId or current state
      const currentUserId = requestUserId || userId;
      if (!currentUserId) {
        throw new Error("User ID is required to send messages");
      }

      try {
        let currentSessionId = requestSessionId || sessionId;

        // Auto-create session if missing
        if (!currentSessionId) {
          console.log("🚀 [CHAT_PROVIDER] No session ID found, creating new session automatically...");
          setIsInitializing(true);
          
          // Show a toast so the user knows what's happening
          const toastId = toast.loading("Creating secure banking session...");
          
          try {
            const { createSessionAction } = await import("@/lib/actions/session-actions");
            const result = await createSessionAction(currentUserId);
            
            if (result.success && result.sessionId) {
              currentSessionId = result.sessionId;
              newlyCreatedSessionIdRef.current = currentSessionId;
              handleSessionSwitch(currentSessionId);
              toast.success("Session created", { id: toastId });
              console.log("✅ [CHAT_PROVIDER] Auto-session created:", currentSessionId);
            } else {
              toast.error("Failed to create session", { id: toastId });
              setIsInitializing(false);
              throw new Error(result.error || "Failed to create auto-session");
            }
          } catch (error) {
            toast.error("Session error", { id: toastId });
            setIsInitializing(false);
            throw error;
          }
        }

        // Add user message to chat immediately
        const userMessage: Message = {
          type: "human",
          content: query,
          id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
          timestamp: new Date(),
        };
        addMessage(userMessage);
        setIsInitializing(false);

        // Submit message for streaming - pass the explicit sessionId
        await streamingManager.submitMessage(query, currentSessionId);
      } catch (error) {
        console.error("Error submitting message:", error);
        setIsInitializing(false);
        
        const errorMsg = error instanceof Error ? error.message : String(error);
        
        if (
          errorMsg.includes("Failed to establish a new connection") ||
          errorMsg.includes("Network is unreachable") ||
          errorMsg.includes("oauth2.googleapis.com")
        ) {
          toast.error("Secure Connection Unreachable", {
            description: "We are unable to connect to Google OAuth servers. Please verify your system's internet connection or cloud credential variables.",
            duration: 6000,
          });
        } else {
          toast.error("Query Execution Failed", {
            description: errorMsg || "We encountered an unexpected error compiling your banking query.",
            duration: 4000,
          });
        }
      }
    },
    [userId, sessionId, addMessage, streamingManager, handleSessionSwitch]
  );

  const handleStopStream = useCallback((): void => {
    streamingManager.stopMessageStream();
  }, [streamingManager]);

  // Context value
  const contextValue: ChatContextValue = {
    // Session state
    userId,
    userEmail,
    sessionId,
    isFirstSession,

    // Message state
    messages,
    messageEvents,
    websiteCount,

    // Loading state
    isLoading: streamingManager.isLoading,
    isLoadingHistory,
    isLoadingAuth,
    isInitializing,
    currentAgent: streamingManager.currentAgent,

    // Session actions
    handleCreateNewSession,
    handleSessionSwitch,
    handleSignOut,

    // Message actions
    handleSubmit,
    handleStopStream,
    addMessage,

    // Refs
    scrollAreaRef,
  };

  return (
    <ChatContext.Provider value={contextValue}>{children}</ChatContext.Provider>
  );
}

/**
 * Custom hook for consuming chat context
 * Provides error handling when used outside provider
 */
export function useChatContext(): ChatContextValue {
  const context = useContext(ChatContext);

  if (!context) {
    throw new Error(
      "useChatContext must be used within a ChatProvider. " +
        "Make sure your component is wrapped with <ChatProvider>."
    );
  }

  return context;
}
