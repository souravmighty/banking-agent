"use client";

import React, { useState, useEffect } from "react";
import { Landmark, Loader2, ShieldCheck, Database, UserCheck, Cpu, Check } from "lucide-react";

interface FirstSessionLoaderProps {
  onComplete?: () => void;
}

export function FirstSessionLoader({ onComplete }: FirstSessionLoaderProps): React.JSX.Element {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: "Verifying secure credentials",
      description: "Authorizing session token with secure verification services...",
      icon: ShieldCheck,
    },
    {
      title: "Accessing financial databases",
      description: "Compiling active account balances, loans, and credit-card ledgers...",
      icon: Database,
    },
    {
      title: "Synthesizing user profile memory",
      description: "Syncing wealth segments and risk profiles into ADK core memory...",
      icon: UserCheck,
    },
    {
      title: "Calibrating Conversational AI",
      description: "Initializing localized safe-inference vectors and security guards...",
      icon: Cpu,
    },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < steps.length - 1) {
          return prev + 1;
        } else {
          clearInterval(timer);
          return prev;
        }
      });
    }, 2000);

    return () => clearInterval(timer);
  }, [steps.length]);

  useEffect(() => {
    if (currentStep === steps.length - 1) {
      // Give the user a moment to see the final step complete before triggering onComplete
      const timeout = setTimeout(() => {
        onComplete?.();
      }, 1500);
      return () => clearTimeout(timeout);
    }
  }, [currentStep, steps.length, onComplete]);

  // Calculate overall progress percentage
  const progressPercent = Math.min(((currentStep + 1) / steps.length) * 100, 100);

  return (
    <div className="h-full w-full flex flex-col items-center justify-center bg-[#1a1f71] text-white px-6 py-12 relative overflow-hidden select-none animate-in fade-in duration-500">
      {/* Abstract banking grids/shapes for premium aesthetic */}
      <div className="absolute inset-0 bg-radial-gradient from-blue-900/40 via-transparent to-transparent pointer-events-none opacity-50" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-800/10 rounded-full -mr-48 -mt-48 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-amber-500/5 rounded-full -ml-48 -mb-48 blur-3xl pointer-events-none" />

      {/* Main loading card */}
      <div className="relative z-10 max-w-lg w-full flex flex-col items-center text-center">
        {/* Glowing animated landmark icon */}
        <div className="relative mb-6">
          <div className="absolute inset-0 rounded-3xl bg-amber-500/20 blur-xl animate-pulse" />
          <div className="w-18 h-18 rounded-3xl bg-white text-[#1a1f71] flex items-center justify-center shadow-2xl relative border border-white/10 ring-4 ring-white/5 animate-bounce">
            <Landmark className="h-9 w-9 text-[#1a1f71]" />
          </div>
          <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-amber-500 text-[#1a1f71] flex items-center justify-center shadow-lg border border-[#1a1f71] animate-spin">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          </div>
        </div>

        {/* Title Section */}
        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-white mb-2">
          Initializing Secure Session Context
        </h2>
        <p className="text-xs md:text-sm text-slate-300 max-w-md mb-8 leading-relaxed">
          Please wait while the AI compiles your banking profile. This occurs only on your first query to build a secure context mapping via <span className="font-semibold text-amber-400">secure verification protocols</span>.
        </p>

        {/* Progress Bar */}
        <div className="w-full max-w-md h-1.5 bg-white/10 rounded-full overflow-hidden mb-8 p-px">
          <div 
            className="h-full bg-gradient-to-r from-amber-400 to-amber-500 rounded-full transition-all duration-500 ease-out shadow-[0_0_8px_rgba(240,165,0,0.5)]"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Dynamic Checklist Card */}
        <div className="w-full max-w-md bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-5 md:p-6 text-left space-y-4 shadow-xl">
          {steps.map((item, idx) => {
            const isCompleted = idx < currentStep;
            const isActive = idx === currentStep;

            return (
              <div 
                key={idx} 
                className={`flex items-start gap-4 transition-all duration-300 ${
                  isCompleted ? "opacity-60" : isActive ? "opacity-100 scale-[1.01]" : "opacity-30"
                }`}
              >
                {/* Status Indicator Icon */}
                <div className="flex-shrink-0 mt-0.5">
                  {isCompleted ? (
                    <div className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-sm shadow-emerald-500/20">
                      <Check className="h-3 w-3 stroke-[3]" />
                    </div>
                  ) : isActive ? (
                    <div className="w-5 h-5 rounded-full bg-amber-500 text-[#1a1f71] flex items-center justify-center">
                      <Loader2 className="h-3 w-3 stroke-[2.5] animate-spin" />
                    </div>
                  ) : (
                    <div className="w-5 h-5 rounded-full bg-white/10 border border-white/10 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-white/40" />
                    </div>
                  )}
                </div>

                {/* Text Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold tracking-wide ${
                      isCompleted ? "text-slate-300 line-through decoration-slate-400/50" : isActive ? "text-amber-400" : "text-white/60"
                    }`}>
                      {item.title}
                    </span>
                    {isActive && (
                      <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 animate-pulse border border-amber-500/20">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5 font-medium leading-normal">
                    {item.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Security Footer Badge */}
        <div className="mt-8 flex items-center gap-2 text-white/40">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span className="text-[10px] font-bold tracking-widest uppercase">SSL 256-Bit Encrypted Secure Session</span>
        </div>
      </div>
    </div>
  );
}
