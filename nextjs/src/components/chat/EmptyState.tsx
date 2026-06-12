"use client";

import {
  ArrowRightLeft,
  BadgeHelp,
  CreditCard,
  Landmark,
  LockKeyhole,
  ShieldCheck,
  WalletCards,
} from "lucide-react";

/**
 * EmptyState - AI Goal Planner welcome screen
 * Extracted from ChatMessagesView empty state section
 * Displays when no messages exist in the current session
 */
export function EmptyState(): React.JSX.Element {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 text-center min-h-[60vh]">
      <div className="max-w-6xl w-full space-y-6">
        {/* Hero banner */}
        <section className="rounded-[18px] bg-[#1a1f71] p-8 text-white shadow-sm ring-1 ring-[#d0d3ea]">
          <div className="mx-auto flex max-w-3xl flex-col items-center gap-4 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#252b82] text-[#f0a500] shadow-inner ring-1 ring-white/10">
              <Landmark className="h-[28px] w-[28px]" />
            </div>
            <h1 className="text-[24px] font-medium tracking-[0.02em] text-white">Your secure banking assistant</h1>
            <p className="text-[13px] text-[#c8cadf]">Your 24/7 banking companion — accounts, payments, and answers, all in one place.</p>
          </div>
          <div className="mt-6 h-[2px] w-full bg-[#f0a500]" />
        </section>

        {/* Description */}
        <div className="space-y-4">
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Ask anything about your account, transactions, payments, or banking guidance. The experience stays simple, secure, and easy to follow.
          </p>
        </div>

        {/* Capability cards */}
        <section className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {[
            {title: 'Account & transactions', icon: WalletCards, items: ['Balance overview', 'Recent transactions', 'Disputes & statements']},
            {title: 'Payments & transfers', icon: ArrowRightLeft, items: ['Transfers', 'Credit card bill', 'Schedule & status']},
            {title: 'Products & FAQs', icon: BadgeHelp, items: ['Savings comparison', 'Card benefits', 'Loan info & rates']},
          ].map(({title, icon: Icon, items}) => (
            <article key={title} className="rounded-[12px] border border-[#d0d3ea] bg-white p-4 text-left shadow-sm">
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-[8px] bg-[#edeffe] text-[#1a1f71]">
                  <Icon className="h-[16px] w-[16px]" />
                </div>
                <h3 className="text-[12px] font-medium uppercase tracking-[0.08em] text-[#1a1f71]">{title}</h3>
              </div>
              <ul className="space-y-2 text-[11px] text-[#6b6f99]">
                {items.map((item) => (
                  <li key={item} className="flex items-start gap-2 border-t border-[#d0d3ea] pt-2 first:border-t-0 first:pt-0">
                    <span className="mt-1.5 h-1 w-1 rounded-full bg-[#f0a500]" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </section>

        <div className="h-px w-full bg-[#d0d3ea]" />

        <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {[
            {label: 'Credit card questions', icon: CreditCard},
            {label: 'Transfer status updates', icon: ArrowRightLeft},
            {label: 'Rates & fees', icon: BadgeHelp},
            {label: 'Secure payments', icon: LockKeyhole},
          ].map((item) => (
            <article key={item.label} className="rounded-[12px] border border-[#d0d3ea] bg-white p-4 text-left text-[12px] text-[#3a3f6e] shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-[8px] bg-[#edeffe] text-[#1a1f71]">
                  <item.icon className="h-[14px] w-[14px]" />
                </div>
                <span>{item.label}</span>
              </div>
            </article>
          ))}
        </section>

        <section className="rounded-[12px] bg-[#252b82] px-4 py-3 text-left text-[12px] text-[#c8cadf] shadow-sm">
          <div className="flex items-center gap-3"> 
            <ShieldCheck className="h-[14px] w-[14px] text-[#f0a500]" />
            <span>Your data is protected with secure banking-grade privacy controls.</span>
          </div>
        </section>
      </div>
    </div>
  );
}
