/**
 * Agent Engine Handler for Run SSE API Route
 *
 * Handles requests for Agent Engine deployment configuration.
 * This handler processes streaming JSON fragments from Agent Engine and converts them to SSE format.
 * Note: Agent Engine returns JSON fragments (not standard SSE), so we parse and reformat them.
 */

import { getEndpointForPath, getAuthHeaders } from "@/lib/config";
import {
  ProcessedStreamRequest,
  formatAgentEnginePayload,
  logStreamStart,
  logStreamResponse,
  SSE_HEADERS,
} from "./run-sse-common";
import {
  createInternalServerError,
  createBackendConnectionError,
} from "./error-utils";

/**
 * Agent Engine JSON Fragment Types
 * Based on the actual format Agent Engine returns
 */
interface AgentEngineContentPart {
  text?: string;
  thought?: boolean;
  function_call?: {
    name: string;
    args: Record<string, unknown>;
    id: string;
  };
  function_response?: {
    name: string;
    response: Record<string, unknown>;
    id: string;
  };
}

interface AgentEngineFragment {
  content?: {
    parts?: AgentEngineContentPart[];
  };
  role?: string;
  author?: string;
  usage_metadata?: {
    candidates_token_count?: number;
    prompt_token_count?: number;
    total_token_count?: number;
    thoughts_token_count?: number;
  };
  invocation_id?: string;
  actions?: {
    state_delta?: Record<string, unknown>;
    artifact_delta?: Record<string, unknown>;
    requested_auth_configs?: Record<string, unknown>;
  };
  isFinal?: boolean; // Added for the new processor
}

/**
 * Processes JSON fragments from Agent Engine streaming response.
 * Agent Engine sends a single large JSON object with parts.
 * We look for complete part objects and stream them immediately when found.
 *
 * IMPROVED VERSION: Uses native JSON.parse() instead of manual brace counting
 * for better reliability and performance.
 */
class JSONFragmentProcessor {
  private buffer: string = "";
  private currentAgent: string = "";
  private sentParts: Set<string> = new Set(); // Track sent parts by their content hash

  constructor(
    private controller: ReadableStreamDefaultController<Uint8Array>
  ) {}

  /**
   * Process incoming chunk of data from Agent Engine.
   * Accumulates chunks and looks for complete fragments to process.
   */
  processChunk(chunk: string): void {
    console.log(`🔄 [JSON PROCESSOR] Processing chunk: ${chunk.length} bytes`);
    console.log(
      `📝 [JSON PROCESSOR] Full chunk content:`,
      JSON.stringify(chunk)
    );

    this.buffer += chunk;

    // Use robust fragment-level parsing approach
    this.extractCompleteFragmentsFromBuffer();
  }

  /**
   * Extract complete fragment objects from buffer by counting curly braces.
   * This handles nested objects, string literals, and escaped characters.
   */
  private extractCompleteFragmentsFromBuffer(): void {
    let searchPos = 0;
    while (searchPos < this.buffer.length) {
      const startIdx = this.buffer.indexOf("{", searchPos);
      if (startIdx === -1) {
        // No start brace found, clear buffer if it's just whitespace/newlines
        if (!this.buffer.trim()) {
          this.buffer = "";
        }
        break;
      }

      let braceCount = 0;
      let inString = false;
      let escapeNext = false;
      let matchIdx = -1;

      for (let i = startIdx; i < this.buffer.length; i++) {
        const char = this.buffer[i];

        if (escapeNext) {
          escapeNext = false;
          continue;
        }

        if (char === "\\") {
          escapeNext = true;
          continue;
        }

        if (char === '"') {
          inString = !inString;
          continue;
        }

        if (!inString) {
          if (char === "{") {
            braceCount++;
          } else if (char === "}") {
            braceCount--;
            if (braceCount === 0) {
              matchIdx = i;
              break;
            }
          }
        }
      }

      if (matchIdx !== -1) {
        const jsonStr = this.buffer.substring(startIdx, matchIdx + 1);
        try {
          const fragment: AgentEngineFragment = JSON.parse(jsonStr);
          this.processCompleteFragment(fragment);
        } catch (error) {
          console.error(
            "❌ [JSON PROCESSOR] Failed to parse complete fragment JSON:",
            error
          );
        }
        // Consume this part of the buffer
        this.buffer = this.buffer.substring(matchIdx + 1);
        searchPos = 0; // Reset search position as buffer changed
      } else {
        // Matching closing brace not found yet, wait for more data
        break;
      }
    }
  }

  /**
   * Create a simple hash of a part to detect duplicates
   */
  private hashPart(part: AgentEngineContentPart): string {
    if (part.function_call) {
      return `func-call-${part.function_call.id || part.function_call.name}`;
    }
    if (part.function_response) {
      return `func-resp-${part.function_response.id || part.function_response.name}`;
    }
    const textHash = part.text?.substring(0, 100) || "";
    return `${textHash}-${part.thought}-${textHash.length}`;
  }

  /**
   * Emit a complete part as SSE format to the frontend
   * Converts from Agent Engine JSON fragments to standard SSE format
   */
  private emitCompletePart(part: AgentEngineContentPart): void {
    console.log(
      `📤 [JSON PROCESSOR] Emitting complete part as SSE format (thought: ${part.thought}):`,
      part.text?.substring(0, 200) +
        (part.text && part.text.length > 200 ? "..." : "")
    );

    const sseData = {
      content: {
        parts: [part],
      },
      author: this.currentAgent || "goal_planning_agent",
    };

    // Convert to proper SSE format: data: {...}\n\n
    const sseEvent = `data: ${JSON.stringify(sseData)}\n\n`;
    this.controller.enqueue(Buffer.from(sseEvent));

    console.log(
      `✅ [JSON PROCESSOR] Successfully emitted complete part as SSE format`
    );
  }

  /**
   * Process a complete JSON fragment (called when we have a full/valid response chunk)
   */
  processCompleteFragment(fragment: AgentEngineFragment): void {
    console.log(
      `✅ [JSON PROCESSOR] Processing complete fragment for agent: ${fragment.author}`
    );
    console.log(`📋 [JSON PROCESSOR] Complete fragment content:`, fragment);

    this.currentAgent = fragment.author || "goal_planning_agent";

    // Process the actual content parts (text thoughts, function calls, function responses)
    if (fragment.content?.parts && Array.isArray(fragment.content.parts)) {
      console.log(
        `🔍 [JSON PROCESSOR] Found ${fragment.content.parts.length} parts in complete fragment`
      );

      for (const [index, part] of fragment.content.parts.entries()) {
        if (
          (part.text && typeof part.text === "string") ||
          part.function_call ||
          part.function_response
        ) {
          const partHash = this.hashPart(part);

          if (!this.sentParts.has(partHash)) {
            console.log(
              `✅ [JSON PROCESSOR] Processing complete fragment part ${
                index + 1
              } (thought: ${part.thought}): ${part.text?.substring(0, 100) || "no-text"}...`
            );
            this.emitCompletePart(part);
            this.sentParts.add(partHash);
          } else {
            console.log(
              `⏭️ [JSON PROCESSOR] Skipping duplicate part ${index + 1}`
            );
          }
        }
      }
    } else {
      console.log(
        `⚠️ [JSON PROCESSOR] No content.parts found in complete fragment`
      );
    }

    // Stream any additional data (actions, usage_metadata, etc.)
    if (
      fragment.actions ||
      fragment.usage_metadata ||
      fragment.invocation_id ||
      fragment.isFinal
    ) {
      const additionalData: Record<string, unknown> = {
        author: fragment.author || "goal_planning_agent",
      };

      if (fragment.actions) additionalData.actions = fragment.actions;
      if (fragment.usage_metadata)
        additionalData.usage_metadata = fragment.usage_metadata;
      if (fragment.invocation_id)
        additionalData.invocation_id = fragment.invocation_id;
      if (fragment.isFinal) additionalData.isFinal = fragment.isFinal;

      console.log(`📤 [JSON PROCESSOR] Emitting final metadata as SSE format`);
      const sseEvent = `data: ${JSON.stringify(additionalData)}\n\n`;
      this.controller.enqueue(Buffer.from(sseEvent));
    }

    // Log token usage if available
    if (fragment.usage_metadata) {
      console.log("📊 [JSON PROCESSOR] Token usage:", fragment.usage_metadata);
    }
  }

  /**
   * Finalize the stream processing
   */
  finalize(): void {
    console.log("🏁 [JSON PROCESSOR] Finalizing stream");

    // Try to extract any remaining fragments
    this.extractCompleteFragmentsFromBuffer();

    // Fallback parser if there is any remaining text in buffer
    if (this.buffer.trim()) {
      try {
        const fragment: AgentEngineFragment = JSON.parse(this.buffer);
        this.processCompleteFragment(fragment);
        this.buffer = "";
      } catch (error) {
        console.error(
          "❌ [JSON PROCESSOR] Failed to parse remaining buffer on finalize:",
          this.buffer,
          error
        );
      }
    }
  }
}

/**
 * Handle Agent Engine streaming request with JSON fragment processing
 *
 * @param requestData - Processed request data
 * @returns Streaming SSE Response with processed JSON fragments
 */
export async function handleAgentEngineStreamRequest(
  requestData: ProcessedStreamRequest
): Promise<Response> {
  console.log(
    "🚀🚀🚀 [AGENT ENGINE] NEW JSON FRAGMENT HANDLER STARTING 🚀🚀🚀"
  );
  console.log(
    `📊 [AGENT ENGINE] Request data:`,
    JSON.stringify(requestData, null, 2)
  );

  try {
    // Format payload for Agent Engine
    const agentEnginePayload = formatAgentEnginePayload(requestData);

    // Build Agent Engine URL with the streamQuery endpoint
    const agentEngineUrl = getEndpointForPath("", "streamQuery");

    // Log operation start
    logStreamStart(agentEngineUrl, agentEnginePayload, "agent_engine");

    // Get authentication headers
    const authHeaders = await getAuthHeaders();

    // Forward request to Agent Engine streaming endpoint
    const response = await fetch(agentEngineUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
        ...(requestData.idToken ? { "X-Firebase-Id-Token": requestData.idToken } : {}),
      },
      body: JSON.stringify(agentEnginePayload),
    });

    // Log the response from Agent Engine
    logStreamResponse(
      response.status,
      response.statusText,
      response.headers,
      "agent_engine"
    );

    // Check for errors from Agent Engine
    if (!response.ok) {
      let errorDetails = `Agent Engine returned an error: ${response.status} ${response.statusText}`;
      try {
        const errorText = await response.text();
        console.error(`❌ Agent Engine error details:`, errorText);
        if (errorText) {
          errorDetails += `. ${errorText}`;
        }
      } catch (error) {
        // Response body might not be available or already consumed
        console.error(
          "An error occurred while trying to read the error response body from Agent Engine:",
          error
        );
      }
      return createBackendConnectionError(
        "agent_engine",
        response.status,
        response.statusText,
        errorDetails
      );
    }

    // Create streaming response that processes JSON fragments
    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          controller.error(new Error("No readable stream from Agent Engine"));
          return;
        }

        console.log(
          "🚀🚀🚀 [AGENT ENGINE] Starting JSON fragment processing 🚀🚀🚀"
        );
        console.log(
          "📋 [AGENT ENGINE] This is the NEW handler with JSONFragmentProcessor"
        );

        // Initialize JSON fragment processor
        const processor = new JSONFragmentProcessor(controller);

        // Set up timeout mechanism (5 minutes max)
        const timeoutMs = 5 * 60 * 1000; // 5 minutes
        const startTime = Date.now();
        let isStreamActive = true;

        try {
          // Read and process JSON fragments using recursive pump pattern with timeout
          const pump = async (): Promise<void> => {
            // Check for timeout
            if (Date.now() - startTime > timeoutMs) {
              console.error("❌ [AGENT ENGINE] Stream timeout after 5 minutes");
              processor.finalize();
              controller.close();
              return;
            }

            if (!isStreamActive) {
              return;
            }

            const { done, value } = await reader.read();

            if (value) {
              const chunk = decoder.decode(value, { stream: true });
              console.log(
                `⏰ [STREAMING] Received chunk at ${new Date().toISOString()}, size: ${
                  chunk.length
                } bytes`
              );
              processor.processChunk(chunk);
            }

            if (done) {
              console.log("✅ [AGENT ENGINE] JSON fragment stream completed");
              processor.finalize();
              controller.close();
              isStreamActive = false;
              return;
            }

            // Continue processing next chunk
            return pump();
          };

          await pump();
        } catch (error) {
          console.error(
            "❌ [AGENT ENGINE] JSON fragment processing error:",
            error
          );

          // Attempt graceful error recovery
          try {
            processor.finalize();
          } catch (finalizeError) {
            console.error(
              "❌ [AGENT ENGINE] Error during finalization:",
              finalizeError
            );
          }

          controller.error(error);
        } finally {
          isStreamActive = false;
          reader.releaseLock();
        }
      },
    });

    // Return streaming SSE response with proper headers
    return new Response(stream, {
      status: 200,
      headers: SSE_HEADERS,
    });
  } catch (error) {
    console.error("❌ Agent Engine handler error:", error);

    if (error instanceof TypeError && error.message.includes("fetch")) {
      return createBackendConnectionError(
        "agent_engine",
        500,
        "Connection failed",
        "Failed to connect to Agent Engine"
      );
    }

    return createInternalServerError(
      "agent_engine",
      error,
      "Failed to process Agent Engine streaming request"
    );
  }
}
