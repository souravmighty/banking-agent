"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, onAuthStateChanged } from "firebase/auth";
import { auth } from "@/firebase/config";
import { authService } from "@/lib/services/authService";
import { customerIdentityService, CustomerMeResponse } from "@/lib/services/customerIdentityService";
import { useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";
import { Landmark, Loader2 } from "lucide-react";

interface AuthContextType {
  user: User | null;
  customerContext: CustomerMeResponse | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<CustomerMeResponse>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshContext: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const publicRoutes = ["/login", "/demo", "/staff/login", "/staff/setup-password"];

const isStaffEmail = (email: string): boolean => {
  const adminEmails = ["souravmaiti1997@gmail.com", "souravmaiti1997@googlemail.com"];
  const lowerEmail = email.toLowerCase();
  return adminEmails.includes(lowerEmail);
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [customerContext, setCustomerContext] = useState<CustomerMeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Helper to fetch/refresh customer profile context
  const fetchCustomerContext = async (currentUser: User): Promise<boolean> => {
    // Note: Staff might login with accounts that are pre-verified or manually created,
    // but we support emailVerified as standard.
    if (!currentUser.emailVerified) {
      setCustomerContext(null);
      return false;
    }
    try {
      const email = currentUser.email;
      if (!email) {
        throw new Error("No email associated with this account.");
      }

      // Check if they are a staff user first (via static/quick list)
      if (isStaffEmail(email)) {
        setCustomerContext({
          customer_id: 0,
          name: currentUser.displayName || "Bank Staff",
          email: email,
          kyc_status: "VERIFIED",
          customer_segment: "STAFF"
        });
        return true;
      }

      // Check if they are an existing bank customer or dynamic staff fallback
      const checkRes = await customerIdentityService.checkEmail(email);
      
      if (checkRes.is_staff) {
        setCustomerContext({
          customer_id: 0,
          name: currentUser.displayName || "Bank Staff",
          email: email,
          kyc_status: "VERIFIED",
          customer_segment: "STAFF"
        });
        return true;
      }

      if (!checkRes.customer_exists) {
        toast.error("Not a valid bank customer. Please contact your bank.");
        await authService.logout();
        setCustomerContext(null);
        return false;
      }

      const token = await currentUser.getIdToken();

      // If they exist but are not registered/linked yet (first login with Google/Email), perform backend linking
      if (!checkRes.already_registered) {
        try {
          await customerIdentityService.linkUser(token);
        } catch (linkError) {
          console.error("Auto-linking on sign-in failed:", linkError);
          toast.error("Failed to link customer identity context.");
          await authService.logout();
          setCustomerContext(null);
          return false;
        }
      }

      // Fetch the customer context
      const context = await customerIdentityService.getMe(token);
      setCustomerContext(context);
      return false;
    } catch (error) {
      console.error("Failed to fetch customer identity context on load:", error);
      toast.error("Identity Service Unavailable. Please contact support.");
      setCustomerContext(null);
      return false;
    }
  };

  // Sync auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      
      if (currentUser) {
        if (currentUser.emailVerified) {
          setLoading(true);
          const isStaffUser = await fetchCustomerContext(currentUser);
          
          // Redirect logic after auth
          if (publicRoutes.includes(pathname)) {
            // Check redirect parameter in URL
            const params = new URLSearchParams(window.location.search);
            const redirectUrl = params.get("redirect");
            
            if (redirectUrl) {
              router.push(redirectUrl);
            } else if (isStaffUser) {
              router.push("/staff/demo-requests");
            } else {
              router.push("/");
            }
          }
        } else {
          // Force logout/unauthenticated state if not verified
          setCustomerContext(null);
          if (!publicRoutes.includes(pathname)) {
            router.push("/login");
          }
        }
      } else {
        setCustomerContext(null);
        // Redirect to login if on protected page
        if (!publicRoutes.includes(pathname)) {
          if (pathname.startsWith("/staff/")) {
            router.push(`/staff/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`);
          } else {
            router.push("/login");
          }
        }
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, [pathname, router]);

  // Wrapper for login
  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const context = await authService.login(email, password);
      setCustomerContext(context);
      // Wait for auth state change to set user and redirect
      return context;
    } catch (error) {
      toast.error((error as Error).message || "Login failed");
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Wrapper for registration
  const register = async (email: string, password: string) => {
    try {
      await authService.register(email, password);
    } catch (error) {
      toast.error((error as Error).message || "Registration failed");
      throw error;
    }
  };

  // Wrapper for logout
  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      setCustomerContext(null);
      setUser(null);
      router.push("/login");
    } catch (error) {
      console.error("Logout failed:", error);
      toast.error("Logout failed");
    } finally {
      setLoading(false);
    }
  };

  // Force-refresh customer context
  const refreshContext = async () => {
    if (auth.currentUser) {
      await fetchCustomerContext(auth.currentUser);
    }
  };

  const value = {
    user,
    customerContext,
    loading,
    login,
    register,
    logout,
    refreshContext,
  };

  return (
    <AuthContext.Provider value={value}>
      {loading ? (
        <AuthLoader />
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
}

export function AuthLoader(): React.JSX.Element {
  const [step, setStep] = useState(0);

  const steps = [
    "Establishing secure TLS handshake...",
    "Verifying single sign-on credentials...",
    "Retrieving customer identity context...",
    "Decrypting personal banking context...",
    "Synchronizing secure dashboard data...",
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 1200);
    return () => clearInterval(interval);
  }, [steps.length]);

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-[#f7f8fc]">
      <div className="flex flex-col items-center max-w-sm w-full p-6 text-center">
        {/* Animated logo container */}
        <div className="w-14 h-14 rounded-2xl bg-[#1a1f71] text-white flex items-center justify-center animate-bounce shadow-xl mb-6">
          <Landmark className="h-8 w-8" />
        </div>

        {/* Header */}
        <h2 className="text-md font-extrabold text-[#1a1f71] tracking-tight mb-1">
          Securing Your Session
        </h2>
        <p className="text-[11px] text-slate-500 max-w-xs leading-relaxed mb-6">
          Please wait while we perform compliance checks and synchronize your private ledger parameters.
        </p>

        {/* Step list card */}
        <div className="w-full bg-white border border-slate-100 p-4 rounded-2xl shadow-sm text-left space-y-3">
          {steps.map((text, idx) => {
            const isDone = idx < step;
            const isActive = idx === step;

            return (
              <div key={idx} className="flex items-center gap-2.5 transition-opacity duration-300">
                {isDone ? (
                  <div className="flex-shrink-0 w-4 h-4 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-[9px] font-extrabold">
                    ✓
                  </div>
                ) : isActive ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-[#f0a500] flex-shrink-0" />
                ) : (
                  <div className="h-1.5 w-1.5 rounded-full bg-slate-200 ml-1.5 mr-1 flex-shrink-0" />
                )}
                <span
                  className={`text-xs font-semibold ${
                    isDone
                      ? "text-slate-400 line-through decoration-slate-100"
                      : isActive
                      ? "text-[#1a1f71] font-bold"
                      : "text-slate-400 font-medium"
                  }`}
                >
                  {text}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
