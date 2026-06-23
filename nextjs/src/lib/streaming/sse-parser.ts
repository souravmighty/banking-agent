/**
 * SSE Parser Utilities
 *
 * This module handles the extraction and parsing of Server-Sent Event (SSE) data.
 * It contains complex JSON parsing logic for various types of SSE messages
 * including text content, thoughts, function calls, and function responses.
 */

import { ParsedSSEData, RawSSEData } from "./types";

/**
 * Sanitizes raw SSE data that may contain invalid JSON formatting.
 * For example, backend errors formatted as JSON can have unescaped nested double quotes:
 * {"error": "ConnectionError(... NewConnectionError("... Failed to establish..."))"}
 *
 * This function extracts the error message, escapes it properly, and reconstructs a valid JSON string.
 */
function sanitizeSSEData(data: string): string {
  const trimmed = data.trim();
  if (trimmed.startsWith('{"error":') && trimmed.endsWith('}')) {
    const errorPrefix = '"error":';
    const prefixIndex = trimmed.indexOf(errorPrefix);
    if (prefixIndex !== -1) {
      const valStartIdx = trimmed.indexOf('"', prefixIndex + errorPrefix.length);
      const valEndIdx = trimmed.lastIndexOf('"');
      if (valStartIdx !== -1 && valEndIdx !== -1 && valEndIdx > valStartIdx) {
        const errorContent = trimmed.substring(valStartIdx + 1, valEndIdx);
        // Normalize first (unescape backslashes/quotes to raw representation to prevent double-escaping)
        const normalized = errorContent.replace(/\\"/g, '"').replace(/\\\\/g, '\\');
        // Re-escape properly for JSON
        const escaped = normalized
          .replace(/\\/g, '\\\\')
          .replace(/"/g, '\\"')
          .replace(/\n/g, '\\n')
          .replace(/\r/g, '\\r')
          .replace(/\t/g, '\\t');
        return `{"error": "${escaped}"}`;
      }
    }
  }
  return data;
}

/**
 * Extracts and processes data from SSE JSON strings
 *
 * This function handles the complex parsing of SSE data received from the backend,
 * extracting various types of content including regular text, AI thoughts,
 * function calls/responses, and source information.
 *
 * @param data - Raw SSE data string to parse
 * @returns Structured data object with extracted information
 */
export function extractDataFromSSE(data: string): ParsedSSEData {
  try {
    const sanitizedData = sanitizeSSEData(data);
    const parsed: RawSSEData = JSON.parse(sanitizedData);

    console.log("📄 [SSE PARSER] Raw parsed JSON:", {
      hasContent: !!parsed.content,
      hasParts: !!(parsed.content && parsed.content.parts),
      partsLength: parsed.content?.parts?.length || 0,
      author: parsed.author,
      id: parsed.id,
      error: parsed.error,
      rawData: JSON.stringify(parsed, null, 2),
    });

    if (parsed.error) {
      return {
        messageId: undefined,
        textParts: [],
        thoughtParts: [],
        agent: "",
        error: parsed.error,
      };
    }

    let textParts: string[] = [];
    let agent = "";
    let functionCall = undefined;
    let functionResponse = undefined;

    // Extract message ID from backend
    const messageId = parsed.id;

    // Extract text from content.parts (separate thoughts from regular text)
    let thoughtParts: string[] = [];
    if (parsed.content && parsed.content.parts) {
      console.log("🔍 [SSE PARSER] Processing content.parts:", {
        partsCount: parsed.content.parts.length,
        parts: parsed.content.parts.map(
          (part: { text?: string; thought?: boolean }, index: number) => ({
            index,
            hasText: !!part.text,
            hasThought: !!part.thought,
            thoughtValue: part.thought,
            textPreview: part.text
              ? part.text.substring(0, 100) + "..."
              : "no text",
          })
        ),
      });

      // ALWAYS filter out thoughts from main text content (like working /web/ project)
      // This ensures thoughts are processed separately as timeline activities
      textParts = parsed.content.parts
        .filter(
          (part: { text?: string; thought?: boolean }) =>
            part.text && !part.thought
        )
        .map((part: { text?: string }) => part.text!)
        .filter((text): text is string => text !== undefined);

      // Extract thoughts separately for timeline activities (for both backends)
      thoughtParts = parsed.content.parts
        .filter(
          (part: { text?: string; thought?: boolean }) =>
            part.text && part.thought
        )
        .map((part: { text?: string }) => part.text!)
        .filter((text): text is string => text !== undefined);

      console.log("🧠 [SSE PARSER] Thought extraction results:", {
        thoughtPartsCount: thoughtParts.length,
        textPartsCount: textParts.length,
        thoughtPreviews: thoughtParts.map((t) => t.substring(0, 50) + "..."),
        textPreviews: textParts.map((t) => t.substring(0, 50) + "..."),
      });

      // Check for function calls
      const functionCallPart = parsed.content.parts.find(
        (part: { functionCall?: unknown }) => part.functionCall
      );
      if (functionCallPart) {
        functionCall = functionCallPart.functionCall as {
          name: string;
          args: Record<string, unknown>;
          id: string;
        };
      }

      // Check for function responses
      const functionResponsePart = parsed.content.parts.find(
        (part: { functionResponse?: unknown }) => part.functionResponse
      );
      if (functionResponsePart) {
        functionResponse = functionResponsePart.functionResponse as {
          name: string;
          response: Record<string, unknown>;
          id: string;
        };
      }
    }

    // Extract agent information
    if (parsed.author) {
      agent = parsed.author;
    }

    return {
      messageId,
      textParts,
      thoughtParts,
      agent,
      functionCall,
      functionResponse,
    };
  } catch (error) {
    return handleSSEParsingError(data, error);
  }
}

/**
 * Handles errors that occur during SSE data parsing
 *
 * @param data - Original data that failed to parse
 * @param error - The parsing error
 * @returns Default parsed data structure with error information logged
 */
function handleSSEParsingError(data: string, error: unknown): ParsedSSEData {
  const truncatedData =
    data.length > 200 ? data.substring(0, 200) + "..." : data;
  console.error(
    'Error parsing SSE data. Raw data (truncated): "',
    truncatedData,
    '". Error details:',
    error
  );

  return {
    messageId: undefined,
    textParts: [],
    thoughtParts: [],
    agent: "",
    functionCall: undefined,
    functionResponse: undefined,
  };
}

/**
 * Validates if a parsed SSE data object is valid
 *
 * @param data - Parsed SSE data to validate
 * @returns True if the data structure is valid, false otherwise
 */
export function validateParsedSSEData(data: ParsedSSEData): boolean {
  return (
    Array.isArray(data.textParts) &&
    Array.isArray(data.thoughtParts) &&
    typeof data.agent === "string"
  );
}

/**
 * Checks if parsed SSE data contains meaningful content
 *
 * @param data - Parsed SSE data to check
 * @returns True if the data contains any meaningful content
 */
export function hasSSEContent(data: ParsedSSEData): boolean {
  return (
    data.textParts.length > 0 ||
    data.thoughtParts.length > 0 ||
    data.functionCall !== undefined ||
    data.functionResponse !== undefined ||
    data.agent !== ""
  );
}
