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
  User, 
  Briefcase, 
  CheckCircle2, 
  ShieldCheck, 
  AlertCircle 
} from "lucide-react";
import { toast } from "sonner";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "@/firebase/config";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const { login, register } = useAuth();
  const router = useRouter();
  const [role, setRole] = useState<"customer" | "staff">("customer");
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleGoogleSignIn = async () => {
    if (role === "staff") {
      toast.info("Google Sign-In is only available for Customers.");
      return;
    }
    
    setIsGoogleLoading(true);
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      await signInWithPopup(auth, googleProvider);
      toast.success("Successfully signed in with Google!");
      router.push("/");
    } catch (error) {
      console.error("Google Auth error:", error);
      const firebaseError = error as { code: string; message?: string };
      if (firebaseError.code !== "auth/popup-closed-by-user") {
        setErrorMessage(firebaseError.message || "Failed to sign in with Google.");
        toast.error("Failed to sign in with Google.");
      }
    } finally {
      setIsGoogleLoading(false);
    }
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMessage(null);
    setErrorMessage(null);

    if (role === "staff") {
      toast.info("Bank Staff login is coming soon!");
      return;
    }

    if (!email || !password) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsLoading(true);
    try {
      if (isSignUp) {
        // Sign Up Flow (Onboarding)
        await register(email, password);
        setStatusMessage("Verification email sent. Please verify your email before logging in.");
        toast.success("Enrollment request submitted! Check your email.");
        // Reset password field
        setPassword("");
        // Switch back to login view so they can sign in after verification
        setIsSignUp(false);
      } else {
        // Log In Flow
        await login(email, password);
        toast.success("Successfully signed in!");
      }
    } catch (error: unknown) {
      console.error("Authentication error:", error);
      const err = error as { message?: string; code?: string };
      const message = err.message || "";
      
      // Map user-friendly error messages based on the response details or Firebase error codes
      if (message.includes("Not a valid bank customer") || message.includes("pre-authorized customer list")) {
        setErrorMessage("Not a valid bank customer. Please contact your bank for assistance.");
        toast.error("Not a valid bank customer.");
      } else if (message.includes("verify your email") || message.includes("Verification email sent")) {
        setStatusMessage("Verification email sent. Please verify your email before logging in.");
        toast.info("Please verify your email address.");
      } else if (err.code === "auth/user-not-found" || err.code === "auth/wrong-password" || err.code === "auth/invalid-credential" || message.includes("Invalid email or password")) {
        setErrorMessage("Invalid email or password.");
        toast.error("Invalid credentials.");
      } else if (err.code === "auth/email-already-in-use" || message.includes("already registered")) {
        setErrorMessage("This email is already in use. Try signing in instead.");
        toast.error("Email already in use.");
      } else if (err.code === "auth/weak-password" || message.includes("Password should be at least 6 characters")) {
        setErrorMessage("Password should be at least 6 characters.");
        toast.error("Weak password.");
      } else if (err.code === "auth/too-many-requests") {
        setErrorMessage("Too many failed attempts. Please try again later.");
        toast.error("Too many failed attempts.");
      } else if (message.includes("Identity Service Unavailable") || message.includes("Failed to fetch") || message.includes("fetch")) {
        setErrorMessage("Identity service is currently unavailable. Please try again later.");
        toast.error("Service unavailable.");
      } else {
        setErrorMessage(message || "An unexpected error occurred. Please try again.");
        toast.error("Authentication failed.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-white font-sans text-slate-900">
      {/* Left Side - Hero Section */}
      <div className="hidden lg:flex lg:w-1/2 bg-[#1a1f71] relative overflow-hidden flex-col justify-between p-12 text-white">
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl bg-white text-[#1a1f71] flex items-center justify-center shadow-lg">
              <Landmark className="h-6 w-6" />
            </div>
            <span className="text-xl font-bold tracking-tight">ABC Bank</span>
          </div>
          
          <h1 className="text-5xl font-bold leading-tight mb-6">
            Build your future <br />
            with ABC Bank.
          </h1>
          <p className="text-lg text-blue-100/80 max-w-md leading-relaxed">
            Experience secure, intelligent, and seamless banking powered by our advanced AI assistant. Your financial goals, simplified.
          </p>
        </div>

        <div className="relative z-10 flex gap-4 items-center">
          <div className="flex -space-x-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="w-10 h-10 rounded-full border-2 border-[#1a1f71] bg-blue-400 flex items-center justify-center text-[10px] font-bold">
                {String.fromCharCode(64 + i)}
              </div>
            ))}
          </div>
          <p className="text-sm text-blue-100/60">
            Trusted by over 2M+ customers worldwide
          </p>
        </div>

        {/* Abstract Background Shapes */}
        <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-gradient-to-br from-blue-500/20 to-transparent blur-3xl opacity-50" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[80%] h-[80%] rounded-full bg-gradient-to-tr from-[#f0a500]/10 to-transparent blur-3xl opacity-30" />
      </div>

      {/* Right Side - Sign In / Sign Up Form */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center p-8 bg-[#f7f8fc] overflow-y-auto">
        <div className="max-w-xl w-full space-y-8 py-10">
          <div className="text-center">
            <div className="lg:hidden flex justify-center mb-6">
              <div className="w-12 h-12 rounded-xl bg-[#1a1f71] text-white flex items-center justify-center shadow-lg">
                <Landmark className="h-7 w-7" />
              </div>
            </div>
            <h2 className="text-4xl font-bold text-[#1a1f71] mb-2 tracking-tight">
              {isSignUp ? "Create Secure Account" : "Welcome Back"}
            </h2>
            <p className="text-[#64748b] font-medium">Please enter your details to proceed</p>
          </div>

          {/* Role Selection */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={() => {
                setRole("customer");
                setErrorMessage(null);
                setStatusMessage(null);
              }}
              className={`relative flex flex-col p-6 rounded-2xl border-2 transition-all text-left bg-white ${
                role === "customer" 
                  ? "border-[#1a1f71] shadow-lg shadow-blue-100 ring-1 ring-[#1a1f71]" 
                  : "border-slate-200 hover:border-slate-300 shadow-sm"
              }`}
            >
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${
                role === "customer" ? "bg-[#1a1f71] text-white" : "bg-slate-100 text-slate-400"
              }`}>
                <User className="h-6 w-6" />
              </div>
              <h3 className={`font-bold text-lg mb-1 ${role === "customer" ? "text-[#1a1f71]" : "text-slate-600"}`}>Customer</h3>
              <p className="text-sm text-[#64748b] leading-relaxed">Manage your accounts, view transactions, and access personalized banking services</p>
              {role === "customer" && (
                <CheckCircle2 className="absolute top-4 right-4 h-6 w-6 text-[#1a1f71]" />
              )}
            </button>

            <button
              onClick={() => {
                setRole("staff");
                setErrorMessage(null);
                setStatusMessage(null);
              }}
              className={`relative flex flex-col p-6 rounded-2xl border-2 transition-all text-left bg-white ${
                role === "staff" 
                  ? "border-[#1a1f71] shadow-lg shadow-blue-100 ring-1 ring-[#1a1f71]" 
                  : "border-slate-200 hover:border-slate-300 shadow-sm"
              }`}
            >
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${
                role === "staff" ? "bg-[#1a1f71] text-white" : "bg-slate-100 text-slate-400"
              }`}>
                <Briefcase className="h-6 w-6" />
              </div>
              <h3 className={`font-bold text-lg mb-1 ${role === "staff" ? "text-[#1a1f71]" : "text-slate-600"}`}>Bank Staff</h3>
              <p className="text-sm text-[#64748b] leading-relaxed">Dedicated portal for administrators, relationship managers, and operations teams</p>
              {role === "staff" && (
                <CheckCircle2 className="absolute top-4 right-4 h-6 w-6 text-[#1a1f71]" />
              )}
            </button>
          </div>

          {/* Permanent Verification Info Section */}
          {statusMessage && statusMessage.includes("Verification email") && (
            <div className="bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-yellow-500/10 border border-amber-200/50 rounded-3xl p-6 shadow-xl shadow-amber-900/5 backdrop-blur-md animate-fade-in-up duration-500">
              <div className="flex gap-4 items-start">
                <div className="w-12 h-12 rounded-2xl bg-amber-500 text-white flex items-center justify-center shadow-lg shadow-amber-500/20 shrink-0">
                  <Mail className="h-6 w-6 animate-pulse" />
                </div>
                <div className="space-y-1.5 min-w-0 flex-1">
                  <h4 className="text-base font-extrabold text-amber-900 tracking-tight flex items-center gap-2">
                    Verify Your Email Address
                  </h4>
                  <p className="text-sm text-amber-800/95 font-semibold leading-relaxed">
                    A secure verification link has been sent to your email. Please open the link in your inbox to verify your account.
                  </p>
                  <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-amber-200/30">
                    <span className="text-xs text-amber-900 font-bold bg-amber-500/20 px-2.5 py-1 rounded-lg">
                      1. Check Inbox & Spam
                    </span>
                    <span className="text-xs text-[#1a1f71] font-bold bg-blue-100/50 px-2.5 py-1 rounded-lg">
                      2. Click Verify Link
                    </span>
                    <span className="text-xs text-emerald-800 font-bold bg-emerald-100/50 px-2.5 py-1 rounded-lg">
                      3. Sign In Below
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <Card className="border-none shadow-2xl shadow-slate-200/50 bg-white rounded-3xl overflow-hidden">
            <CardContent className="p-8 sm:p-10 space-y-8">
              <div className="flex flex-col items-center gap-6">
                <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 text-[#1a1f71] text-xs font-bold uppercase tracking-wider">
                  Access Level: <span className="capitalize">{role}</span>
                </div>

                {role === "customer" && (
                  <Button 
                    variant="outline" 
                    type="button"
                    className="w-full h-12 border-slate-200 hover:bg-slate-50 text-slate-700 font-bold transition-all rounded-xl gap-3 flex items-center justify-center"
                    onClick={handleGoogleSignIn}
                    disabled={isLoading || isGoogleLoading}
                  >
                    {isGoogleLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <svg className="h-5 w-5 animate-pulse-subtle" viewBox="0 0 24 24">
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
                )}
              </div>

              {role === "customer" && (
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-100"></div>
                  </div>
                  <div className="relative flex justify-center text-[10px] uppercase tracking-[0.15em] font-bold text-slate-400">
                    <span className="bg-white px-4">or use your banking credentials</span>
                  </div>
                </div>
              )}

              {/* Status and Error Alerts */}
              {errorMessage && (
                <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 text-red-800 border border-red-100 text-sm">
                  <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Registration Blocked:</span> {errorMessage}
                  </div>
                </div>
              )}

              {statusMessage && (
                <div className="flex items-start gap-3 p-4 rounded-xl bg-green-50 text-green-800 border border-green-100 text-sm">
                  <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Next Steps:</span> {statusMessage}
                  </div>
                </div>
              )}

              <form onSubmit={handleAuth} className="space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-700 ml-1 flex items-center gap-2">
                    <Mail className="h-4 w-4 text-slate-400" />
                    Email Address
                  </label>
                  <Input
                    type="email"
                    placeholder="you@example.com"
                    className="h-12 border-slate-200 focus:border-[#1a1f71] focus:ring-[#1a1f71]/5 transition-all rounded-xl bg-slate-50/50"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center px-1">
                    <label className="text-sm font-bold text-slate-700 flex items-center gap-2">
                      <Lock className="h-4 w-4 text-slate-400" />
                      Password
                    </label>
                  </div>
                  <Input
                    type="password"
                    placeholder="Enter your secure password"
                    className="h-12 border-slate-200 focus:border-[#1a1f71] focus:ring-[#1a1f71]/5 transition-all rounded-xl bg-slate-50/50"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-12 bg-[#1a1f71] hover:bg-[#2a2f81] text-white font-bold transition-all rounded-xl shadow-lg shadow-blue-900/10"
                  disabled={isLoading || isGoogleLoading}
                >
                  {isLoading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <ArrowRight className="mr-2 h-4 w-4" />
                      {role === "staff" 
                        ? "Sign In: Staff Portal" 
                        : isSignUp ? "Enroll and Create Account" : "Access Customer Portal"
                      }
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="text-center space-y-4">
            <p className="text-sm text-[#64748b] font-medium">
              {role === "customer" ? (
                <>
                  {isSignUp ? "Already registered?" : "New to ABC Bank?"}{" "}
                  <button 
                    onClick={() => {
                      setIsSignUp(!isSignUp);
                      setErrorMessage(null);
                      setStatusMessage(null);
                    }}
                    className="font-bold text-[#1a1f71] hover:underline"
                  >
                    {isSignUp ? "Sign In" : "Enroll now"}
                  </button>
                </>
              ) : (
                "Staff portal access is restricted to authorized personnel only."
              )}
            </p>

            <div className="flex items-center justify-center gap-2 text-[11px] text-slate-400 font-bold uppercase tracking-widest pt-4">
              <ShieldCheck className="h-4 w-4" />
              Secure 256-bit SSL encrypted connection
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
