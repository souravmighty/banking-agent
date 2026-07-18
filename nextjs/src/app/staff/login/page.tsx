"use client";

import React, { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Landmark, 
  Mail, 
  Lock, 
  ArrowRight, 
  Loader2, 
  ShieldCheck, 
  AlertCircle 
} from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { signInWithPopup, signOut } from "firebase/auth";
import { auth, googleProvider } from "@/firebase/config";
import { customerIdentityService } from "@/lib/services/customerIdentityService";

export default function StaffLoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    setErrorMessage(null);
    try {
      // 1. Authenticate with Google
      const userCredential = await signInWithPopup(auth, googleProvider);
      const user = userCredential.user;

      if (!user.email) {
        throw new Error("No email associated with this Google account.");
      }

      // 2. Query Identity Service to verify staff status
      const checkRes = await customerIdentityService.checkEmail(user.email);
      if (!checkRes.customer_exists || !checkRes.is_staff) {
        await signOut(auth);
        throw new Error("This Google account is not pre-authorized as bank staff. Please ask an administrator to add your email first.");
      }

      // 3. Link Google account dynamically if firebase_uid has not been set yet
      if (!checkRes.already_registered) {
        const idToken = await user.getIdToken();
        await customerIdentityService.linkStaff(idToken);
        toast.info("Google credentials registered and linked to staff ledger!");
      }

      toast.success("Successfully signed in as Bank Staff!");
      
      // 4. Handle routing
      const params = new URLSearchParams(window.location.search);
      const redirectUrl = params.get("redirect");
      if (redirectUrl) {
        router.push(redirectUrl);
      } else {
        router.push("/staff/demo-requests");
      }
    } catch (error: any) {
      console.error("Staff Google login error:", error);
      if (error.code !== "auth/popup-closed-by-user") {
        setErrorMessage(error.message || "Failed to sign in with Google.");
      }
    } finally {
      setIsGoogleLoading(false);
    }
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email || !password) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsLoading(true);
    try {
      await login(email, password);
      toast.success("Successfully signed in as Bank Staff!");
      
      // Let the AuthProvider handle the query redirect, or fallback:
      const params = new URLSearchParams(window.location.search);
      const redirectUrl = params.get("redirect");
      if (redirectUrl) {
        router.push(redirectUrl);
      } else {
        router.push("/staff/demo-requests");
      }
    } catch (error: unknown) {
      console.error("Staff login error:", error);
      const err = error as { message?: string };
      setErrorMessage(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#05070f] flex flex-col items-center justify-center relative overflow-hidden font-sans text-slate-100 p-4">
      {/* Deep dark mesh background */}
      <div className="absolute top-[-30%] left-[-20%] w-[800px] h-[800px] rounded-full bg-indigo-900/10 blur-[180px] pointer-events-none" />
      <div className="absolute bottom-[-30%] right-[-20%] w-[800px] h-[800px] rounded-full bg-violet-900/10 blur-[180px] pointer-events-none" />

      <div className="w-full max-w-md z-10">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8 text-center animate-fade-in">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shadow-xl shadow-indigo-500/10 mb-4 border border-indigo-400/20">
            <ShieldCheck className="h-7 w-7 text-white animate-pulse" />
          </div>
          <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-500 bg-clip-text text-transparent">
            BankPilot Staff Portal
          </h1>
          <p className="text-xs text-slate-400 max-w-xs mt-2">
            Secure administrative console for request authorization, audit logs, and demo customer pool management.
          </p>
        </div>

        <Card className="border-slate-800/80 bg-slate-900/40 backdrop-blur-xl shadow-2xl rounded-3xl overflow-hidden border">
          <CardContent className="p-8">
            <form onSubmit={handleAuth} className="space-y-5">
              {errorMessage && (
                <div className="flex gap-2 p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 text-rose-400" />
                  <p>{errorMessage}</p>
                </div>
              )}

              {/* Email Input */}
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Staff Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                  <Input
                    type="email"
                    placeholder="name@bankpilot.dev"
                    required
                    disabled={isLoading}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-11 bg-slate-950/50 border-slate-800/80 text-white rounded-xl h-11 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 placeholder:text-slate-600"
                  />
                </div>
              </div>

              {/* Password Input */}
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Staff Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                  <Input
                    type="password"
                    placeholder="••••••••"
                    required
                    disabled={isLoading}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-11 bg-slate-950/50 border-slate-800/80 text-white rounded-xl h-11 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 placeholder:text-slate-600"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={isLoading || isGoogleLoading}
                className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 active:scale-[0.99] transition-all text-white font-bold h-11 rounded-xl border border-indigo-500/20 shadow-lg shadow-indigo-500/10 flex items-center justify-center gap-2 mt-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Authorizing Credentials...
                  </>
                ) : (
                  <>
                    Sign In to Console
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>

              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-800"></div>
                </div>
                <div className="relative flex justify-center text-[9px] uppercase tracking-[0.2em] font-bold text-slate-500">
                  <span className="bg-[#0b0f19] px-3 py-1 rounded-full border border-slate-800/80">or continue with</span>
                </div>
              </div>

              <Button
                variant="outline"
                type="button"
                className="w-full h-11 border-slate-800 bg-slate-950/40 hover:bg-slate-900/50 hover:text-white text-slate-300 font-bold transition-all rounded-xl gap-3 flex items-center justify-center border"
                onClick={handleGoogleSignIn}
                disabled={isLoading || isGoogleLoading}
              >
                {isGoogleLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                ) : (
                  <>
                    <svg className="h-5 w-5 shrink-0" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-1 .67-2.28 1.07-3.71 1.07-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.67-.35-1.39-.35-2.09s.13-1.42.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Continue with Google
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Footer info link */}
        <div className="mt-8 text-center text-[10px] text-slate-600 flex flex-col items-center gap-2">
          <div className="flex items-center gap-1.5 bg-slate-950/40 px-3 py-1 rounded-full border border-slate-900">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
            <span className="font-semibold text-slate-500">Dual-factor hardware token required for out-of-network access.</span>
          </div>
          <p>© 2026 BankPilot Operations. All access sessions are logged for audit compliance.</p>
        </div>
      </div>
    </div>
  );
}
