import { useState, useCallback, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { Message } from "@/types";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { StreamingConnectionManager } from "@/lib/streaming/connection-manager";
import { getEventTitle } from "@/lib/streaming/stream-utils";
import {
  StreamProcessingCallbacks,
  StreamingAPIPayload,
} from "@/lib/streaming/types";

export interface UseStreamingReturn {
  // State
  isLoading: boolean;
  currentAgent: string;

  // Operations
  startStream: (
    apiPayload: { message: string; userId: string; sessionId: string },
    onMessageUpdate: (message: Message) => void,
    onEventUpdate: (messageId: string, event: ProcessedEvent) => void,
    onWebsiteCountUpdate: (count: number) => void
  ) => Promise<void>;

  stopStream: () => void;

  getEventTitle: (agentName: string) => string;
}

/**
 * Custom hook for managing SSE streaming connections and data processing
 */
export function useStreaming(
  retryFn: <T>(fn: () => Promise<T>) => Promise<T>
): UseStreamingReturn {
  // React state management
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [currentAgent, setCurrentAgent] = useState<string>("");

  // Refs to track streaming state
  const accumulatedTextRef = useRef<string>("");
  const currentAgentRef = useRef<string>("");

  // Connection manager instance
  const connectionManager = useRef<StreamingConnectionManager | null>(null);

  // Initialize connection manager if not already created
  if (connectionManager.current === null) {
    connectionManager.current = new StreamingConnectionManager({
      retryFn,
      endpoint: "/api/run_sse",
    });
  }

  // Start streaming operation
  const startStream = useCallback(
    async (
      apiPayload: { message: string; userId: string; sessionId: string },
      onMessageUpdate: (message: Message) => void,
      onEventUpdate: (messageId: string, event: ProcessedEvent) => void,
      onWebsiteCountUpdate: (count: number) => void
    ): Promise<void> => {
      if (!connectionManager.current) {
        throw new Error("Connection manager not initialized");
      }

      // Generate AI message ID (frontend generates ID for streaming correlation)
      const aiMessageId = uuidv4();

      // 🔑 CRITICAL: Initialize the empty AI message in the UI state immediately
      // to dismiss the first-query ContextLoader screen and render the AI Activity Timeline from the start.
      onMessageUpdate({
        type: "ai",
        content: "",
        id: aiMessageId,
        timestamp: new Date(),
      });

      // Create callbacks object for the connection manager
      const callbacks: StreamProcessingCallbacks = {
        onMessageUpdate,
        onEventUpdate,
        onWebsiteCountUpdate,
      };

      // Convert to internal payload format
      const streamingPayload: StreamingAPIPayload = {
        message: apiPayload.message,
        userId: apiPayload.userId,
        sessionId: apiPayload.sessionId,
      };

      // Delegate to connection manager
      const result = await connectionManager.current.submitMessage(
        streamingPayload,
        callbacks,
        accumulatedTextRef,
        currentAgentRef,
        setCurrentAgent,
        setIsLoading,
        aiMessageId
      );

      // 🔑 CRITICAL: If the stream finished and a tool was executed, automatically trigger
      // a secondary connection with the same sessionId and aiMessageId to synthesize the final markdown response.
      // This displays the final synthesized text right under the AI Activity Timeline inside the initial bubble.
      if (result?.hasToolExecution) {
        console.log("🤖 [useStreaming] Tool execution detected. Auto-triggering secondary synthesis connection.");
        
        // Wait 300ms before starting the secondary turn to allow backend to finalize the tool state
        await new Promise((resolve) => setTimeout(resolve, 300));

        const synthesizePayload: StreamingAPIPayload = {
          message: "Please proceed to provide the final synthesized response based on the tool results.",
          userId: apiPayload.userId,
          sessionId: apiPayload.sessionId,
        };

        await connectionManager.current.submitMessage(
          synthesizePayload,
          callbacks,
          accumulatedTextRef,
          currentAgentRef,
          setCurrentAgent,
          setIsLoading,
          aiMessageId
        );
      }
    },
    []
  );

  // Stop streaming operation
  const stopStream = useCallback((): void => {
    if (connectionManager.current) {
      connectionManager.current.cancelRequest(
        accumulatedTextRef,
        currentAgentRef,
        setCurrentAgent,
        setIsLoading
      );
    }
  }, []);

  const getEventTitleCallback = useCallback((agentName: string): string => {
    return getEventTitle(agentName);
  }, []);

  return {
    // State
    isLoading,
    currentAgent,

    // Operations
    startStream,
    stopStream,

    // Utilities
    getEventTitle: getEventTitleCallback,
  };
}
