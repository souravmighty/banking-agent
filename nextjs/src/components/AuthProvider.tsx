"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, onAuthStateChanged } from "firebase/auth";
import { auth } from "@/firebase/config";
import { authService } from "@/lib/services/authService";
import { customerIdentityService, CustomerMeResponse } from "@/lib/services/customerIdentityService";
import { useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";

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

const publicRoutes = ["/login"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [customerContext, setCustomerContext] = useState<CustomerMeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Helper to fetch/refresh customer profile context
  const fetchCustomerContext = async (currentUser: User) => {
    if (!currentUser.emailVerified) {
      setCustomerContext(null);
      return;
    }
    try {
      const email = currentUser.email;
      if (!email) {
        throw new Error("No email associated with this account.");
      }

      // Check if they are an existing bank customer
      const checkRes = await customerIdentityService.checkEmail(email);
      if (!checkRes.customer_exists) {
        toast.error("Not a valid bank customer. Please contact your bank.");
        await authService.logout();
        setCustomerContext(null);
        return;
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
          return;
        }
      }

      // Fetch the customer context
      const context = await customerIdentityService.getMe(token);
      setCustomerContext(context);
    } catch (error) {
      console.error("Failed to fetch customer identity context on load:", error);
      toast.error("Identity Service Unavailable. Please contact support.");
      setCustomerContext(null);
    }
  };

  // Sync auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      
      if (currentUser) {
        if (currentUser.emailVerified) {
          await fetchCustomerContext(currentUser);
          
          // Redirect from login page to dashboard/home if authenticated & verified
          if (publicRoutes.includes(pathname)) {
            router.push("/");
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
          router.push("/login");
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
    setLoading(true);
    try {
      await authService.register(email, password);
    } catch (error) {
      toast.error((error as Error).message || "Registration failed");
      throw error;
    } finally {
      setLoading(false);
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

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
