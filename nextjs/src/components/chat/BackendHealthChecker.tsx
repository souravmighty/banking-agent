"use client";

import { useBackendHealth } from "@/hooks/useBackendHealth";
import { AuthLoader } from "@/components/AuthProvider";

interface BackendHealthCheckerProps {
  onHealthStatusChange?: (isHealthy: boolean, isChecking: boolean) => void;
  children?: React.ReactNode;
}

/**
 * Backend health monitoring component that displays appropriate states
 * Uses the useBackendHealth hook for monitoring and retry logic
 */
export function BackendHealthChecker({
  onHealthStatusChange,
  children,
}: BackendHealthCheckerProps) {
  const { isBackendReady, isCheckingBackend, checkBackendHealth } =
    useBackendHealth();

  // Notify parent of health status changes
  React.useEffect(() => {
    if (onHealthStatusChange) {
      onHealthStatusChange(isBackendReady, isCheckingBackend);
    }
  }, [isBackendReady, isCheckingBackend, onHealthStatusChange]);

  // Show loading screen while checking backend
  if (isCheckingBackend) {
    return <AuthLoader />;
  }

  // Show error screen if backend is not ready
  if (!isBackendReady) {
    return <BackendErrorScreen onRetry={checkBackendHealth} />;
  }

  // Render children if backend is ready
  return <>{children}</>;
}

/**
 * Error screen component shown when backend is unavailable
 */
function BackendErrorScreen({ onRetry }: { onRetry: () => Promise<boolean> }) {
  const handleRetry = () => {
    onRetry().catch((error) => {
      console.error("Retry failed:", error);
    });
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold text-red-400">Backend Unavailable</h2>
        <p className="text-neutral-300">
          Unable to connect to backend services
        </p>
        <button
          onClick={handleRetry}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

// Need to import React for useEffect
import React from "react";
