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

export default function StaffLoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

              {/* Action Button */}
              <Button
                type="submit"
                disabled={isLoading}
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
