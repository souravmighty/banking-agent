"use client";

import React, { useState } from "react";
import { customerIdentityService } from "@/lib/services/customerIdentityService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Landmark, 
  Mail, 
  User, 
  Briefcase, 
  CheckCircle2, 
  ShieldCheck, 
  Linkedin,
  Github,
  ArrowRight,
  Loader2,
  FileText
} from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";

const ROLES = [
  "Recruiter / Talent Acquisition",
  "Hiring Manager",
  "Software Engineer",
  "Senior Software Engineer",
  "AI Engineer",
  "Applied AI Engineer",
  "Machine Learning Engineer",
  "Data Scientist",
  "Data Engineer",
  "Cloud Engineer",
  "Platform Engineer",
  "Product Manager",
  "Student",
  "Researcher",
  "Founder / Entrepreneur",
  "Consultant",
  "Banking Professional",
  "Other"
];

const PURPOSES = [
  "Hiring Evaluation",
  "Technical Evaluation",
  "Exploring AI Banking",
  "Learning Google ADK / Multi-Agent Systems",
  "Research / Academic",
  "Other"
];

export default function DemoPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [otherRole, setOtherRole] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [selectedPurposes, setSelectedPurposes] = useState<string[]>([]);
  const [otherPurpose, setOtherPurpose] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  
  // Client-side validation error states
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = "Full Name is required.";
    }

    if (!email.trim()) {
      newErrors.email = "Business Email is required.";
    } else {
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(email)) {
        newErrors.email = "Please enter a valid email address.";
      }
    }

    if (!role) {
      newErrors.role = "Please select your current role.";
    } else if (role === "Other" && !otherRole.trim()) {
      newErrors.otherRole = "Please specify your role.";
    }

    if (linkedin.trim()) {
      const li = linkedin.toLowerCase();
      if (!li.includes("linkedin.com/") && !li.includes("linkedin.cn/")) {
        newErrors.linkedin = "Please enter a valid LinkedIn profile URL.";
      }
    }

    if (selectedPurposes.length === 0) {
      newErrors.purpose = "Please select at least one purpose of evaluation.";
    } else if (selectedPurposes.includes("Other") && !otherPurpose.trim()) {
      newErrors.otherPurpose = "Please specify your evaluation purpose.";
    }

    if (!acceptedTerms) {
      newErrors.acceptedTerms = "You must acknowledge the synthetic data statement.";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      toast.error("Please resolve the errors in the form.");
      return;
    }

    setErrors({});
    setIsLoading(true);

    const finalRole = role === "Other" ? `Other: ${otherRole}` : role;
    const finalPurpose = selectedPurposes.includes("Other")
      ? [...selectedPurposes.filter(p => p !== "Other"), `Other: ${otherPurpose}`].join(", ")
      : selectedPurposes.join(", ");

    try {
      await customerIdentityService.submitDemoRequest({
        name,
        email,
        company: company || undefined,
        role: finalRole,
        linkedin: linkedin || undefined,
        purpose: finalPurpose,
      });

      setIsSuccess(true);
      toast.success("Demo request submitted successfully!");
    } catch (error) {
      console.error("Demo submission failed:", error);
      toast.error((error as Error).message || "Failed to submit demo request.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0d1d] flex flex-col items-center justify-center relative overflow-hidden font-sans text-slate-100 p-4">
      {/* Decorative ambient background mesh */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-blue-500/10 blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-500/10 blur-[140px] pointer-events-none" />

      <div className="w-full max-w-2xl z-10 my-8">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8 text-center animate-fade-in">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#2563eb] to-[#4f46e5] flex items-center justify-center shadow-xl shadow-blue-500/10 mb-4 border border-blue-400/20">
            <Landmark className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            BankPilot Demo Access
          </h1>
          <p className="text-sm text-slate-400 max-w-md mt-2">
            Experience our next-generation agentic banking backend. Request short-term secure sandbox access.
          </p>
        </div>

        {!isSuccess ? (
          <Card className="border-slate-800/80 bg-slate-900/60 backdrop-blur-xl shadow-2xl rounded-3xl overflow-hidden border">
            <CardContent className="p-8 sm:p-10">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  {/* Name Input */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Full Name <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <User className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                      <Input
                        type="text"
                        placeholder="John Doe"
                        required
                        disabled={isLoading}
                        value={name}
                        onChange={(e) => {
                          setName(e.target.value);
                          if (errors.name) {
                            setErrors(prev => ({ ...prev, name: "" }));
                          }
                        }}
                        className={`pl-11 bg-slate-950/40 border-slate-800/80 text-white rounded-xl h-11 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 placeholder:text-slate-600 ${
                          errors.name ? "border-red-500/60 focus:ring-red-500/20" : ""
                        }`}
                      />
                    </div>
                    {errors.name && (
                      <p className="text-xs text-red-400 mt-1">{errors.name}</p>
                    )}
                  </div>

                  {/* Email Input */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Email Address <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                      <Input
                        type="email"
                        placeholder="john@company.com"
                        required
                        disabled={isLoading}
                        value={email}
                        onChange={(e) => {
                          setEmail(e.target.value);
                          if (errors.email) {
                            setErrors(prev => ({ ...prev, email: "" }));
                          }
                        }}
                        className={`pl-11 bg-slate-950/40 border-slate-800/80 text-white rounded-xl h-11 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 placeholder:text-slate-600 ${
                          errors.email ? "border-red-500/60 focus:ring-red-500/20" : ""
                        }`}
                      />
                    </div>
                    {errors.email && (
                      <p className="text-xs text-red-400 mt-1">{errors.email}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  {/* Company Input */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Company / Institution
                    </label>
                    <div className="relative">
                      <Briefcase className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                      <Input
                        type="text"
                        placeholder="Google, JPMorgan Chase, HSBC, Stanford University, Self-employed..."
                        disabled={isLoading}
                        value={company}
                        onChange={(e) => setCompany(e.target.value)}
                        className="pl-11 bg-slate-950/40 border-slate-800/80 text-white rounded-xl h-11 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 placeholder:text-slate-600"
                      />
                    </div>
                    <p className="text-[11px] text-slate-500">
                      Optional – helps us understand who is exploring BankPilot.
                    </p>
                  </div>

                  {/* Role Dropdown */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Current Role <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <FileText className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                      <select
                        disabled={isLoading}
                        value={role}
                        onChange={(e) => {
                          setRole(e.target.value);
                          if (errors.role) {
                            setErrors(prev => ({ ...prev, role: "" }));
                          }
                        }}
                        className={`w-full pl-11 pr-10 bg-slate-950/40 border-slate-800/80 text-white rounded-xl h-11 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 text-sm focus:outline-none appearance-none cursor-pointer ${
                          errors.role ? "border-red-500/60" : ""
                        }`}
                      >
                        <option value="" disabled className="bg-slate-900 text-slate-400">Select your role...</option>
                        {ROLES.map((r) => (
                          <option key={r} value={r} className="bg-slate-900 text-slate-200">
                            {r}
                          </option>
                        ))}
                      </select>
                      {/* Dropdown caret */}
                      <div className="absolute right-4 top-4.5 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-500 w-0 h-0" />
                    </div>
                    {errors.role && (
                      <p className="text-xs text-red-400 mt-1">{errors.role}</p>
                    )}
                  </div>
                </div>

                {/* Specific Role Input if "Other" is selected */}
                {role === "Other" && (
                  <div className="space-y-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Please specify your role <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <FileText className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                      <Input
                        type="text"
                        placeholder="E.g., Chief Innovation Officer, Academic Dean..."
                        required
                        disabled={isLoading}
                        value={otherRole}
                        onChange={(e) => {
                          setOtherRole(e.target.value);
                          if (errors.otherRole) {
                            setErrors(prev => ({ ...prev, otherRole: "" }));
                          }
                        }}
                        className={`pl-11 bg-slate-950/40 border-slate-800/80 text-white rounded-xl h-11 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 placeholder:text-slate-600 ${
                          errors.otherRole ? "border-red-500/60" : ""
                        }`}
                      />
                    </div>
                    {errors.otherRole && (
                      <p className="text-xs text-red-400 mt-1">{errors.otherRole}</p>
                    )}
                  </div>
                )}

                {/* LinkedIn Input */}
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    LinkedIn Profile URL <span className="text-[10px] text-slate-500">(Optional)</span>
                  </label>
                  <div className="relative">
                    <Linkedin className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                    <Input
                      type="url"
                      placeholder="https://linkedin.com/in/username"
                      disabled={isLoading}
                      value={linkedin}
                      onChange={(e) => {
                        setLinkedin(e.target.value);
                        if (errors.linkedin) {
                          setErrors(prev => ({ ...prev, linkedin: "" }));
                        }
                      }}
                      className={`pl-11 bg-slate-950/40 border-slate-800/80 text-white rounded-xl h-11 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 placeholder:text-slate-600 ${
                        errors.linkedin ? "border-red-500/60" : ""
                      }`}
                    />
                  </div>
                  {errors.linkedin && (
                    <p className="text-xs text-red-400 mt-1">{errors.linkedin}</p>
                  )}
                </div>

                {/* Purpose of Evaluation Checkbox Group */}
                <div className="space-y-3">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Purpose of Evaluation <span className="text-red-500">*</span>
                  </label>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {PURPOSES.map((p) => {
                      const isChecked = selectedPurposes.includes(p);
                      return (
                        <div
                          key={p}
                          onClick={() => {
                            if (isLoading) return;
                            let nextSelected: string[];
                            if (isChecked) {
                              nextSelected = selectedPurposes.filter((item) => item !== p);
                            } else {
                              nextSelected = [...selectedPurposes, p];
                            }
                            setSelectedPurposes(nextSelected);
                            if (errors.purpose) {
                              setErrors(prev => ({ ...prev, purpose: "" }));
                            }
                          }}
                          className={`flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer select-none transition-all duration-200 ${
                            isChecked
                              ? "bg-blue-950/20 border-blue-500/50 text-white shadow-lg shadow-blue-500/5"
                              : "bg-slate-950/20 border-slate-800/80 text-slate-300 hover:border-slate-700 hover:bg-slate-800/20"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            readOnly
                            disabled={isLoading}
                            className="mt-0.5 h-4 w-4 rounded border-slate-800 bg-slate-950/60 text-blue-600 focus:ring-blue-500/30 accent-blue-600 pointer-events-none"
                          />
                          <span className="text-sm font-medium leading-tight">
                            {p}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  {errors.purpose && (
                    <p className="text-xs text-red-400 mt-1">{errors.purpose}</p>
                  )}
                </div>

                {/* Specific Purpose textarea if "Other" checkbox is checked */}
                {selectedPurposes.includes("Other") && (
                  <div className="space-y-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Please specify <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      placeholder="Specify your purpose for evaluating BankPilot..."
                      disabled={isLoading}
                      value={otherPurpose}
                      onChange={(e) => {
                        setOtherPurpose(e.target.value);
                        if (errors.otherPurpose) {
                          setErrors(prev => ({ ...prev, otherPurpose: "" }));
                        }
                      }}
                      rows={3}
                      className={`w-full p-3.5 bg-slate-950/40 border-slate-800/80 text-white rounded-xl focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 placeholder:text-slate-600 text-sm focus:outline-none ${
                        errors.otherPurpose ? "border-red-500/60" : ""
                      }`}
                    />
                    {errors.otherPurpose && (
                      <p className="text-xs text-red-400 mt-1">{errors.otherPurpose}</p>
                    )}
                  </div>
                )}

                {/* Acknowledge Checkbox */}
                <div className={`flex items-start gap-3 p-4 rounded-xl border transition-colors ${
                  errors.acceptedTerms
                    ? "bg-red-950/10 border-red-900/40"
                    : "bg-blue-950/20 border-blue-900/40"
                }`}>
                  <input
                    type="checkbox"
                    id="terms"
                    checked={acceptedTerms}
                    onChange={(e) => {
                      setAcceptedTerms(e.target.checked);
                      if (errors.acceptedTerms) {
                        setErrors(prev => ({ ...prev, acceptedTerms: "" }));
                      }
                    }}
                    disabled={isLoading}
                    className="mt-1 h-4 w-4 rounded border-slate-800 bg-slate-950/60 text-blue-600 focus:ring-blue-500/30 focus:ring-offset-slate-950 accent-blue-600 cursor-pointer"
                  />
                  <label htmlFor="terms" className="text-xs text-slate-300 leading-normal cursor-pointer select-none">
                    <span className="font-bold text-blue-400">Synthetic Data Acknowledgement <span className="text-red-500">*</span>:</span> I understand that all banking, customer, and transaction parameters in this demo portal represent simulated, synthetic banking parameters only. No real fiat values or live bank credentials will be requested or utilized.
                  </label>
                </div>
                {errors.acceptedTerms && (
                  <p className="text-xs text-red-400 mt-1">{errors.acceptedTerms}</p>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:scale-[0.99] transition-transform text-white font-bold h-12 rounded-xl border border-blue-500/20 shadow-lg shadow-blue-500/10 flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Processing Request...
                    </>
                  ) : (
                    <>
                      Request Sandbox Access
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : (
          /* Success Screen */
          <Card className="border-emerald-900/40 bg-emerald-950/10 backdrop-blur-xl shadow-2xl rounded-3xl overflow-hidden border text-center p-10 max-w-lg mx-auto animate-scale-in">
            <CardContent className="p-0 flex flex-col items-center">
              <div className="w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-6 animate-pulse border border-emerald-500/20">
                <CheckCircle2 className="h-10 w-10" />
              </div>
              <h2 className="text-2xl font-extrabold text-white mb-3">
                Request Received!
              </h2>
              <p className="text-sm text-slate-300 leading-relaxed mb-6">
                Thanks, <span className="font-bold text-white">{name}</span>. Your demo request for <span className="text-blue-400 font-semibold">{email}</span> has been logged. Our operations team has been notified.
              </p>
              
              <div className="w-full p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-left text-slate-400 space-y-2 mb-6">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                  <span className="font-semibold text-slate-300">Identity Context Security:</span>
                </div>
                <p className="pl-6">
                  Once approved, you will receive an automatic email invitation. You can then log in using your Google account to access your personal sandboxed customer environment.
                </p>
              </div>

              {/* GitHub and LinkedIn Quick Badges inside Success Card */}
              <div className="w-full p-4.5 rounded-xl bg-slate-900/60 border border-slate-800/80 mb-6 space-y-3 text-center">
                <p className="text-xs text-slate-400 font-semibold leading-relaxed">
                  While your request is being processed, feel free to explore the repository & connect with me!
                </p>
                <div className="flex justify-center items-center gap-3">
                  <a
                    href="https://github.com/souravmighty/banking-agent"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-slate-950/80 hover:bg-slate-950 hover:text-white border border-slate-800/80 text-slate-300 font-bold text-xs px-3.5 py-2.5 rounded-xl transition-all duration-200"
                  >
                    <Github className="w-4 h-4 text-white" />
                    ⭐ GitHub Source
                  </a>
                  <a
                    href="https://www.linkedin.com/in/souravmaiti/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-[#0a66c2]/10 hover:bg-[#0a66c2]/20 border border-[#0a66c2]/20 text-[#0c73dc] font-bold text-xs px-3.5 py-2.5 rounded-xl transition-all duration-200"
                  >
                    <Linkedin className="w-4 h-4 text-[#0c73dc]" />
                    💼 LinkedIn Profile
                  </a>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 w-full justify-center">
                <Link href="/" className="w-full">
                  <Button className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold h-11 rounded-xl border border-slate-700/50">
                    Back to Portal
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-slate-500 space-y-3">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-2 max-w-md mx-auto">
            <span className="font-medium text-slate-400">Built with ❤️ by <strong className="font-extrabold text-slate-300">Sourav Maiti</strong></span>
            <div className="flex items-center gap-3">
              <a
                href="https://github.com/souravmighty/banking-agent"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-slate-200 flex items-center gap-1 font-bold transition-colors"
              >
                <Github className="w-3.5 h-3.5" />
                GitHub
              </a>
              <span className="text-slate-600">&bull;</span>
              <a
                href="https://www.linkedin.com/in/souravmaiti/"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-slate-200 flex items-center gap-1 font-bold transition-colors"
              >
                <Linkedin className="w-3.5 h-3.5" />
                LinkedIn
              </a>
            </div>
          </div>
          <p>© 2026 BankPilot Systems. Simulated sandbox environment. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
