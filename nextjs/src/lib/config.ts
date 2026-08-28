/**
 * Environment-based configuration for Next.js API endpoints
 * Handles both local development and cloud deployment contexts
 */

export interface EndpointConfig {
  backendUrl: string;
  agentEngineUrl?: string;
  environment: "local" | "cloud";
  deploymentType: "local" | "agent_engine" | "cloud_run";
}

/**
 * Detects the current deployment environment based on available environment variables
 */
function detectEnvironment(): EndpointConfig["environment"] {
  // Check for Google Cloud deployment indicators
  if (
    process.env.GOOGLE_CLOUD_PROJECT ||
    process.env.K_SERVICE ||
    process.env.FUNCTION_NAME
  ) {
    return "cloud";
  }

  // Default to local development
  return "local";
}

/**
 * Detects the deployment type based on environment variables
 */
function detectDeploymentType(): EndpointConfig["deploymentType"] {
  // Check for Agent Engine deployment (only use endpoint)
  if (process.env.AGENT_ENGINE_ENDPOINT) {
    return "agent_engine";
  }

  // Check for Cloud Run deployment
  if (process.env.K_SERVICE || process.env.CLOUD_RUN_SERVICE) {
    return "cloud_run";
  }

  // Default to local development
  return "local";
}

/**
 * Gets the backend URL based on deployment context
 */
export function getBackendUrl(appName?: string): string {
  // If requesting analytics copilot specifically
  if (
    appName === "analytics_copilot_2" ||
    appName === "analytics-copilot-2" ||
    appName === "analytics_copilot" ||
    appName === "analytics-copilot"
  ) {
    return (
      process.env.ANALYTICS_COPILOT_BACKEND_URL ||
      process.env.BACKEND_URL ||
      "http://127.0.0.1:8002"
    );
  }

  const deploymentType = detectDeploymentType();

  switch (deploymentType) {
    case "agent_engine":
      // Agent Engine endpoint - only use the specific endpoint
      if (process.env.AGENT_ENGINE_ENDPOINT) {
        return process.env.AGENT_ENGINE_ENDPOINT;
      }
      throw new Error(
        "AGENT_ENGINE_ENDPOINT environment variable is required for Agent Engine deployment"
      );

    case "cloud_run":
      // Cloud Run deployment - use the service URL
      if (process.env.CLOUD_RUN_SERVICE_URL) {
        return process.env.CLOUD_RUN_SERVICE_URL;
      }
      break;

    case "local":
    default:
      // Local development - use configured backend URL or default
      return process.env.BACKEND_URL || "http://127.0.0.1:8000";
  }

  // Fallback to default local development URL
  return process.env.BACKEND_URL || "http://127.0.0.1:8000";
}

/**
 * Gets the Agent Engine URL for direct Agent Engine API calls
 */
function getAgentEngineUrl(): string | undefined {
  // Only use the direct endpoint, no more individual env var construction
  return process.env.AGENT_ENGINE_ENDPOINT || undefined;
}

/**
 * Creates the endpoint configuration based on current environment
 */
export function createEndpointConfig(): EndpointConfig {
  const environment = detectEnvironment();
  const deploymentType = detectDeploymentType();

  const config: EndpointConfig = {
    backendUrl: getBackendUrl(),
    agentEngineUrl: getAgentEngineUrl(),
    environment,
    deploymentType,
  };

  // Log configuration in development
  if (process.env.NODE_ENV === "development") {
    console.log("🔧 Endpoint Configuration:", {
      environment: config.environment,
      deploymentType: config.deploymentType,
      backendUrl: config.backendUrl,
      agentEngineUrl: config.agentEngineUrl,
    });
  }

  return config;
}

/**
 * Get the current endpoint configuration
 */
export const endpointConfig = createEndpointConfig();

/**
 * Utility to check if a URL is a Vertex AI Reasoning Engine endpoint
 */
export function isReasoningEngineUrl(url?: string): boolean {
  if (!url) return false;
  return url.includes("reasoningEngines") || url.includes("aiplatform.googleapis.com");
}

/**
 * Gets the configured Agent Engine endpoint for a given app
 */
export function getAgentEngineEndpointForApp(appName?: string): string | undefined {
  const isAnalyticsCopilot =
    appName === "analytics_copilot_2" ||
    appName === "analytics-copilot-2" ||
    appName === "analytics_copilot" ||
    appName === "analytics-copilot";

  if (isAnalyticsCopilot) {
    if (process.env.ANALYTICS_COPILOT_AGENT_ENGINE_ENDPOINT) {
      return process.env.ANALYTICS_COPILOT_AGENT_ENGINE_ENDPOINT;
    }
    if (isReasoningEngineUrl(process.env.ANALYTICS_COPILOT_BACKEND_URL)) {
      return process.env.ANALYTICS_COPILOT_BACKEND_URL;
    }
  }

  if (process.env.AGENT_ENGINE_ENDPOINT) {
    return process.env.AGENT_ENGINE_ENDPOINT;
  }
  if (isReasoningEngineUrl(process.env.BACKEND_URL)) {
    return process.env.BACKEND_URL;
  }

  return undefined;
}

/**
 * Utility function to get authentication headers for Google Cloud API calls
 */
export async function getAuthHeaders(targetUrl?: string): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const isGcpEndpoint =
    (targetUrl && isReasoningEngineUrl(targetUrl)) ||
    endpointConfig.deploymentType === "agent_engine" ||
    Boolean(process.env.AGENT_ENGINE_ENDPOINT || process.env.ANALYTICS_COPILOT_AGENT_ENGINE_ENDPOINT);

  if (isGcpEndpoint) {
    try {
      const { GoogleAuth } = await import("google-auth-library");
      let auth;

      if (process.env.GOOGLE_SERVICE_ACCOUNT_KEY_BASE64) {
        const serviceAccountKeyJson = Buffer.from(
          process.env.GOOGLE_SERVICE_ACCOUNT_KEY_BASE64,
          "base64"
        ).toString("utf-8");
        const credentials = JSON.parse(serviceAccountKeyJson);
        auth = new GoogleAuth({
          credentials,
          scopes: ["https://www.googleapis.com/auth/cloud-platform"],
        });
      } else {
        auth = new GoogleAuth({
          scopes: ["https://www.googleapis.com/auth/cloud-platform"],
        });
      }

      const authClient = await auth.getClient();
      const accessToken = await authClient.getAccessToken();

      if (accessToken.token) {
        headers["Authorization"] = `Bearer ${accessToken.token}`;
      }
    } catch (error) {
      console.warn("Could not automatically retrieve Google Cloud access token:", error);
    }
  }

  return headers;
}

/**
 * Determines if we should use Agent Engine API directly for a specific agent
 */
export function shouldUseAgentEngine(appName?: string): boolean {
  if (getAgentEngineEndpointForApp(appName)) {
    return true;
  }
  return (
    endpointConfig.deploymentType === "agent_engine" &&
    Boolean(endpointConfig.agentEngineUrl)
  );
}

/**
 * Agent Engine endpoint types
 */
export type AgentEngineEndpointType = "query" | "streamQuery" | "sessions";

/**
 * Gets the Agent Engine sessions API base URL (v1beta1)
 */
function getAgentEngineSessionsUrl(customEndpoint?: string): string | undefined {
  const targetUrl = customEndpoint || endpointConfig.agentEngineUrl;
  if (!targetUrl) return undefined;

  const urlParts = targetUrl.match(
    /^(https:\/\/[^\/]+)\/v1\/(projects\/[^\/]+\/locations\/[^\/]+\/reasoningEngines\/[^\/]+)/
  );

  if (urlParts) {
    const [, baseUrl, projectPath] = urlParts;
    return `${baseUrl}/v1beta1/${projectPath}`;
  }

  return undefined;
}

/**
 * Gets the appropriate endpoint for a given API path and operation type
 */
export function getEndpointForPath(
  path: string,
  endpointType: AgentEngineEndpointType = "streamQuery",
  appName?: string
): string {
  const agentEngineEndpoint = getAgentEngineEndpointForApp(appName) || endpointConfig.agentEngineUrl;

  if (shouldUseAgentEngine(appName) && agentEngineEndpoint) {
    const cleanEndpoint = agentEngineEndpoint
      .replace(/\/+$/, "")
      .replace(/:(streamQuery|query)$/, "");

    if (endpointType === "streamQuery") {
      return `${cleanEndpoint}:streamQuery`;
    } else if (endpointType === "query") {
      return `${cleanEndpoint}:query`;
    } else if (endpointType === "sessions") {
      const sessionsUrl = getAgentEngineSessionsUrl(cleanEndpoint);
      if (!sessionsUrl) {
        throw new Error(
          `Could not construct sessions API URL from ${cleanEndpoint}`
        );
      }
      return `${sessionsUrl}/sessions${path}`;
    }
  }

  if (appName) {
    const backendUrl = getBackendUrl(appName);
    return `${backendUrl}${path}`;
  }

  return `${endpointConfig.backendUrl}${path}`;
}

/**
 * Gets the Agent Engine streaming endpoint for chat responses
 */
export function getAgentEngineStreamEndpoint(appName?: string): string {
  return getEndpointForPath("", "streamQuery", appName);
}

