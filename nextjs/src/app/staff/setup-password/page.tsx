"use client";

import React, { useState } from "react";
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, sendEmailVerification, signOut } from "firebase/auth";
import { auth } from "@/firebase/config";
import { customerIdentityService } from "@/lib/services/customerIdentityService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { 
  ShieldCheck, 
  Mail, 
  Lock, 
  ArrowRight, 
  Loader2, 
  AlertCircle, 
  Sparkles, 
  CheckCircle2,
  KeyRound
} from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

export default function StaffSetupPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // 1. Client-side basic validation
    if (!email || !password || !confirmPassword) {
      toast.error("Please fill in all fields");
      return;
    }

    if (password.length < 6) {
      setErrorMessage("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      // 2. Pre-verify email status with Identity Service
      const checkRes = await customerIdentityService.checkEmail(email);
      
      if (!checkRes.customer_exists || !checkRes.is_staff) {
        throw new Error("This email is not authorized as bank staff. Please ask an administrator to add your email to the database first.");
      }

      if (checkRes.already_registered) {
        throw new Error("This staff account is already registered. Please go to the login portal instead.");
      }

      // 3. Create Firebase user account (with auto-link fallback for existing Firebase profiles)
      let user;
      try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        user = userCredential.user;
      } catch (fbError: unknown) {
        const err = fbError as { code?: string };
        if (err.code === "auth/email-already-in-use") {
          try {
            // The email already exists in Firebase, try logging in with the entered password to link it!
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            user = userCredential.user;
            toast.info("Existing account recognized. Syncing and linking credentials...");
          } catch {
            throw new Error("This email is already in use in Firebase, but the password entered does not match. If you have forgotten your password, please request an administrator to reset your credentials.");
          }
        } else {
          throw fbError;
        }
      }

      // 4. Retrieve ID Token and update dynamic BigQuery staff mapping
      const idToken = await user.getIdToken();
      await customerIdentityService.linkStaff(idToken);

      // 5. Send out verification email
      try {
        auth.languageCode = "en";
        await sendEmailVerification(user);
      } catch (emailError) {
        console.error("Verification email triggered warning:", emailError);
      }

      // 6. Force Firebase signout so their session remains locked until verified and logged in at standard page
      await signOut(auth);
      
      // Onboarding completed successfully!
      setIsSuccess(true);
      toast.success("Staff security profile successfully created!");
    } catch (error: unknown) {
      console.error("Staff setup exception:", error);
      const err = error as { message?: string };
      setErrorMessage(err.message || "Failed to set up credentials. Please contact your operations administrator.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen w-full bg-[#05070f] flex flex-col items-center justify-center relative overflow-hidden font-sans text-slate-100 p-4">
        {/* Deep dark mesh background */}
        <div className="absolute top-[-30%] left-[-20%] w-[800px] h-[800px] rounded-full bg-emerald-950/10 blur-[180px] pointer-events-none" />
        <div className="absolute bottom-[-30%] right-[-20%] w-[800px] h-[800px] rounded-full bg-violet-900/10 blur-[180px] pointer-events-none" />

        <div className="w-full max-w-md z-10 text-center animate-fade-in">
          <div className="w-16 h-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-indigo-600 flex items-center justify-center shadow-xl shadow-emerald-500/10 mx-auto mb-6 border border-emerald-400/20">
            <CheckCircle2 className="h-8 w-8 text-white" />
          </div>

          <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-white via-slate-200 to-emerald-400 bg-clip-text text-transparent">
            Credentials Established
          </h1>
          <p className="text-sm text-slate-400 max-w-sm mx-auto mt-3 leading-relaxed">
            Your login password has been set up, and your security token is linked to the <code className="text-emerald-400 font-semibold font-mono">bank_staff</code> ledger.
          </p>

          <Card className="border-slate-800/80 bg-slate-900/20 backdrop-blur-xl shadow-2xl rounded-3xl overflow-hidden border mt-8 text-left">
            <CardContent className="p-6 space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
                  1
                </div>
                <div className="text-xs">
                  <h3 className="font-bold text-slate-200">Verify Your Identity</h3>
                  <p className="text-slate-400 mt-1 leading-normal">
                    We&apos;ve dispatched an verification link to <span className="text-indigo-400 font-semibold">{email}</span>. Click the link to authorize your profile.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 border-t border-slate-800/60 pt-4">
                <div className="w-5 h-5 rounded-full bg-indigo-950/40 text-indigo-400 border border-indigo-900/50 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
                  2
                </div>
                <div className="text-xs">
                  <h3 className="font-bold text-slate-200">Access Management Console</h3>
                  <p className="text-slate-400 mt-1 leading-normal">
                    Once verified, navigate to the Operations Login to access requested demo customer approvals and compliance reporting.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Button
            onClick={() => router.push("/staff/login")}
            className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold h-11 rounded-xl border border-indigo-500/20 shadow-lg shadow-indigo-500/10 flex items-center justify-center gap-2 mt-8 active:scale-[0.99] transition-all"
          >
            Go to Operations Login
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#05070f] flex flex-col items-center justify-center relative overflow-hidden font-sans text-slate-100 p-4">
      {/* Deep dark mesh background */}
      <div className="absolute top-[-30%] left-[-20%] w-[800px] h-[800px] rounded-full bg-indigo-900/10 blur-[180px] pointer-events-none" />
      <div className="absolute bottom-[-30%] right-[-20%] w-[800px] h-[800px] rounded-full bg-violet-900/10 blur-[180px] pointer-events-none" />

      <div className="w-full max-w-md z-10">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8 text-center animate-fade-in">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shadow-xl shadow-indigo-500/10 mb-4 border border-indigo-400/20">
            <KeyRound className="h-7 w-7 text-white animate-pulse" />
          </div>
          <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-500 bg-clip-text text-transparent">
            Onboard Bank Staff
          </h1>
          <p className="text-xs text-slate-400 max-w-xs mt-2">
            Dynamic profile initialization. Set your secure passcode to link your operations token.
          </p>
        </div>

        <Card className="border-slate-800/80 bg-slate-900/40 backdrop-blur-xl shadow-2xl rounded-3xl overflow-hidden border">
          <CardContent className="p-8">
            <form onSubmit={handleSetup} className="space-y-5">
              {errorMessage && (
                <div className="flex gap-2 p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 text-rose-400" />
                  <p>{errorMessage}</p>
                </div>
              )}

              {/* Email Input */}
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Pre-Authorized Staff Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                  <Input
                    type="email"
                    placeholder="name@company.com"
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
                  Choose Login Password
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

              {/* Confirm Password Input */}
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                  <Input
                    type="password"
                    placeholder="••••••••"
                    required
                    disabled={isLoading}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
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
                    Linking Account Token...
                  </>
                ) : (
                  <>
                    Complete Staff Setup
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
            <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
            <span className="font-semibold text-slate-500">Only emails added by Admin can complete onboarding.</span>
          </div>
          <p>© 2026 BankPilot Operations. Access tokens are cryptographically linked.</p>
        </div>
      </div>
    </div>
  );
}
