import { useState, useCallback, useEffect } from "react";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "@/firebase/config";
import { useRouter } from "next/navigation";

export interface UseSessionReturn {
  // State
  sessionId: string;
  userId: string;
  isLoadingAuth: boolean;

  // Session management
  handleSessionSwitch: (newSessionId: string) => void;
  handleCreateNewSession: (sessionUserId: string) => Promise<void>;
  handleSignOut: () => Promise<void>;
}

/**
 * Custom hook for managing chat sessions and user ID synced with Firebase Auth
 */
export function useSession(): UseSessionReturn {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);

  // Sync userId with Firebase Auth
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setUserId(user.email || user.uid);
      } else {
        setUserId("");
        // Redirect to login if not authenticated
        router.push("/login");
      }
      setIsLoadingAuth(false);
    });

    return () => unsubscribe();
  }, [router]);

  // Handle session switching
  const handleSessionSwitch = useCallback(
    (newSessionId: string): void => {
      console.log(
        `🔄 handleSessionSwitch called: current=${sessionId}, new=${newSessionId}, userId=${userId}`
      );

      if (!userId || newSessionId === sessionId) {
        console.log(`⏭️ Skipping session switch: no userId or same session`);
        return;
      }

      // Switch to new session
      console.log(`🎯 Setting sessionId state to: ${newSessionId}`);
      setSessionId(newSessionId);

      console.log(`✅ Session switch completed to: ${newSessionId}`);
    },
    [userId, sessionId]
  );

  // Handle new session creation
  const handleCreateNewSession = useCallback(
    async (sessionUserId: string): Promise<void> => {
      if (!sessionUserId) {
        throw new Error("User ID is required to create a session");
      }

      let actualSessionId = "";

      try {
        // Import Server Action dynamically to avoid circular dependencies in hooks
        const { createSessionAction } = await import(
          "@/lib/actions/session-actions"
        );

        const sessionResult = await createSessionAction(sessionUserId);

        if (sessionResult.success) {
          // Use the session ID returned by the backend
          if (!sessionResult.sessionId) {
            throw new Error(
              "Session creation succeeded but no session ID was returned"
            );
          }
          actualSessionId = sessionResult.sessionId;
          console.log(
            `✅ Session created via Server Action: ${actualSessionId}`
          );
        } else {
          console.error(
            "❌ Session creation Server Action failed:",
            sessionResult.error
          );
          throw new Error(`Session creation failed: ${sessionResult.error}`);
        }
      } catch (error) {
        console.error("❌ Session creation Server Action error:", error);
        throw error;
      }

      console.log(`🔄 Switching to new session: ${actualSessionId}`);
      handleSessionSwitch(actualSessionId);
    },
    [handleSessionSwitch]
  );

  // Handle sign out
  const handleSignOut = useCallback(async (): Promise<void> => {
    try {
      await signOut(auth);
      setSessionId("");
      router.push("/login");
    } catch (error) {
      console.error("Error signing out:", error);
    }
  }, [router]);

  return {
    // State
    sessionId,
    userId,
    isLoadingAuth,

    // Session management
    handleSessionSwitch,
    handleCreateNewSession,
    handleSignOut,
  };
}
