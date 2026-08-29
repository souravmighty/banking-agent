"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, onAuthStateChanged } from "firebase/auth";
import { auth } from "@/firebase/config";
import { authService } from "@/lib/services/authService";
import { customerIdentityService, CustomerMeResponse } from "@/lib/services/customerIdentityService";
import { useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";
import { Landmark, Loader2 } from "lucide-react";

export type Persona = "CUSTOMER" | "STAFF";

interface AuthContextType {
  user: User | null;
  customerContext: CustomerMeResponse | null;
  loading: boolean;
  isStaff: boolean;
  hasCustomerAccount: boolean;
  activePersona: Persona | null;
  switchPersona: (target: Persona) => Promise<void>;
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
  const [isStaff, setIsStaff] = useState<boolean>(false);
  const [hasCustomerAccount, setHasCustomerAccount] = useState<boolean>(false);
  const [activePersona, setActivePersona] = useState<Persona | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  // Helper to fetch/refresh identity context and resolve active persona
  const fetchCustomerContext = async (currentUser: User, overridePersona?: Persona): Promise<Persona | null> => {
    if (!currentUser.emailVerified) {
      setCustomerContext(null);
      return null;
    }
    try {
      const email = currentUser.email;
      if (!email) {
        throw new Error("No email associated with this account.");
      }

      // Check role entitlements from Identity Service
      const checkRes = await customerIdentityService.checkEmail(email);
      const isStaffUser = Boolean(checkRes.is_staff || isStaffEmail(email));
      const isCustomerUser = Boolean(checkRes.customer_exists);

      setIsStaff(isStaffUser);
      setHasCustomerAccount(isCustomerUser);

      // Resolve intended persona
      const storedPersona = typeof window !== "undefined" ? (sessionStorage.getItem("auth_persona") as Persona | null) : null;
      let targetPersona = overridePersona || storedPersona;

      if (!targetPersona) {
        targetPersona = pathname.startsWith("/staff") ? "STAFF" : "CUSTOMER";
      }

      if (targetPersona === "STAFF") {
        if (!isStaffUser) {
          if (pathname.startsWith("/staff")) {
            toast.error("This account is not authorized as bank staff.");
            await authService.logout();
            setCustomerContext(null);
            return null;
          }
          // If not staff but has customer account, fallback to customer persona
          if (isCustomerUser) {
            targetPersona = "CUSTOMER";
          }
        } else {
          if (typeof window !== "undefined") {
            sessionStorage.setItem("auth_persona", "STAFF");
          }
          setActivePersona("STAFF");
          const staffContext: CustomerMeResponse = {
            customer_id: 0,
            name: currentUser.displayName || "Bank Staff",
            email: email,
            kyc_status: "VERIFIED",
            customer_segment: "STAFF"
          };
          setCustomerContext(staffContext);
          return "STAFF";
        }
      }

      if (targetPersona === "CUSTOMER") {
        if (!isCustomerUser) {
          if (isStaffUser) {
            // Staff attempting to use customer portal without a customer account
            if (pathname === "/login") {
              toast.error("This email is registered as Bank Staff with no personal customer account. Please use Staff Login.");
              await authService.logout();
              setCustomerContext(null);
              return null;
            }
            // Auto fallback to STAFF persona
            if (typeof window !== "undefined") {
              sessionStorage.setItem("auth_persona", "STAFF");
            }
            setActivePersona("STAFF");
            setCustomerContext({
              customer_id: 0,
              name: currentUser.displayName || "Bank Staff",
              email: email,
              kyc_status: "VERIFIED",
              customer_segment: "STAFF"
            });
            return "STAFF";
          } else {
            toast.error("Not a valid bank customer. Please contact your bank.");
            await authService.logout();
            setCustomerContext(null);
            return null;
          }
        }

        const token = await currentUser.getIdToken();

        // Perform backend linking if not yet registered
        if (!checkRes.already_registered) {
          try {
            await customerIdentityService.linkUser(token);
          } catch (linkError) {
            console.error("Auto-linking on sign-in failed:", linkError);
            toast.error("Failed to link customer identity context.");
            await authService.logout();
            setCustomerContext(null);
            return null;
          }
        }

        // Fetch the customer context
        const context = await customerIdentityService.getMe(token);
        if (typeof window !== "undefined") {
          sessionStorage.setItem("auth_persona", "CUSTOMER");
        }
        setActivePersona("CUSTOMER");
        setCustomerContext(context);
        return "CUSTOMER";
      }

      return null;
    } catch (error) {
      console.error("Failed to fetch customer identity context on load:", error);
      toast.error("Identity Service Unavailable. Please contact support.");
      setCustomerContext(null);
      return null;
    }
  };

  // Sync auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      
      if (currentUser) {
        if (currentUser.emailVerified) {
          setLoading(true);
          const activePersonaResult = await fetchCustomerContext(currentUser);
          
          // Redirect logic after auth
          if (publicRoutes.includes(pathname) && activePersonaResult) {
            const params = new URLSearchParams(window.location.search);
            const redirectUrl = params.get("redirect");
            
            if (redirectUrl) {
              router.push(redirectUrl);
            } else if (activePersonaResult === "STAFF") {
              router.push("/staff/copilot");
            } else {
              router.push("/");
            }
          }
        } else {
          setCustomerContext(null);
          if (!publicRoutes.includes(pathname)) {
            router.push("/login");
          }
        }
      } else {
        setCustomerContext(null);
        setIsStaff(false);
        setHasCustomerAccount(false);
        setActivePersona(null);
        // Redirect to login if on protected page
        if (!publicRoutes.includes(pathname)) {
          if (pathname.startsWith("/staff/")) {
            const redirectParam = encodeURIComponent(
              pathname + (typeof window !== "undefined" ? window.location.search : "")
            );
            router.push(`/staff/login?redirect=${redirectParam}`);
          } else {
            router.push("/login");
          }
        }
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, [pathname, router]);

  // Switch between Customer and Staff persona for dual-role accounts
  const switchPersona = async (target: Persona) => {
    if (!user) return;
    setLoading(true);
    try {
      if (target === "STAFF") {
        if (!isStaff) {
          toast.error("Account not authorized for staff access.");
          return;
        }
        if (typeof window !== "undefined") {
          sessionStorage.setItem("auth_persona", "STAFF");
        }
        setActivePersona("STAFF");
        setCustomerContext({
          customer_id: 0,
          name: user.displayName || "Bank Staff",
          email: user.email || "",
          kyc_status: "VERIFIED",
          customer_segment: "STAFF"
        });
        toast.info("Switched to Bank Staff Portal");
        router.push("/staff/copilot");
      } else {
        if (!hasCustomerAccount) {
          toast.error("No personal banking customer account linked to this email.");
          return;
        }
        const token = await user.getIdToken();
        const context = await customerIdentityService.getMe(token);
        if (typeof window !== "undefined") {
          sessionStorage.setItem("auth_persona", "CUSTOMER");
        }
        setActivePersona("CUSTOMER");
        setCustomerContext(context);
        toast.info("Switched to Personal Banking View");
        router.push("/");
      }
    } catch (err) {
      console.error("Persona switch error:", err);
      toast.error("Failed to switch portal persona.");
    } finally {
      setLoading(false);
    }
  };

  // Wrapper for login
  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const context = await authService.login(email, password);
      setCustomerContext(context);
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
      const isStaffView = typeof window !== "undefined" && (
        window.location.pathname.startsWith("/staff") || 
        sessionStorage.getItem("auth_persona") === "STAFF"
      );
      if (typeof window !== "undefined") {
        sessionStorage.removeItem("auth_persona");
      }
      await authService.logout();
      setCustomerContext(null);
      setUser(null);
      setIsStaff(false);
      setHasCustomerAccount(false);
      setActivePersona(null);
      const target = isStaffView ? "/staff/login" : "/login";
      if (typeof window !== "undefined") {
        window.location.href = target;
      } else {
        router.push(target);
      }
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
    isStaff,
    hasCustomerAccount,
    activePersona,
    switchPersona,
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
