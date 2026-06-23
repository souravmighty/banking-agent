"use client";

import {
  ArrowRightLeft,
  BadgeHelp,
  Landmark,
  ShieldCheck,
  WalletCards,
  Receipt,
  ShoppingBag,
  CreditCard,
  TrendingUp,
} from "lucide-react";
import { useChatContext } from "@/components/chat/ChatProvider";

/**
 * EmptyState - AI Goal Planner welcome screen
 * Extracted from ChatMessagesView empty state section
 * Displays when no messages exist in the current session
 */
export function EmptyState(): React.JSX.Element {
  const { handleSubmit } = useChatContext();

  return (
    <div className="flex-1 flex flex-col items-center p-4 md:p-8 overflow-y-auto">
      <div className="max-w-4xl w-full space-y-10 py-6 md:py-10">
        {/* Hero banner */}
        <section className="rounded-3xl bg-[#1a1f71] p-6 md:p-14 text-white shadow-xl relative overflow-hidden">
          {/* Decorative background elements */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-32 -mt-32 blur-3xl" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-[#f0a500]/10 rounded-full -ml-24 -mb-24 blur-3xl" />
          
          <div className="relative z-10 flex flex-col items-center gap-6 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10 backdrop-blur-md text-[#f0a500] shadow-xl ring-1 ring-white/20">
              <Landmark className="h-8 w-8" />
            </div>
            <div className="space-y-3">
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">ABC Bank Assistant</h1>
              <p className="text-sm md:text-base text-[#c8cadf] max-w-2xl mx-auto leading-relaxed">
                Your 24/7 banking companion — accounts, payments, and answers, all in one place
              </p>
            </div>
          </div>
        </section>

        <div className="space-y-8">
          <section className="space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-[0.15em] text-[#6b6f99] px-1">What I can help you with</h2>
            
            {/* Capability cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
              {[
                {
                  title: 'Account & transactions', 
                  icon: WalletCards, 
                  items: ['Check account balance', 'View recent transactions', 'Dispute a charge', 'Download statements']
                },
                {
                  title: 'Payments & transfers', 
                  icon: ArrowRightLeft, 
                  items: ['Transfer between accounts', 'Pay credit card bill', 'Schedule a payment', 'Track payment status']
                },
                {
                  title: 'Products & FAQs', 
                  icon: BadgeHelp, 
                  items: ['Compare savings accounts', 'Credit card benefits', 'Loan eligibility info', 'Interest rates & fees']
                },
              ].map(({title, icon: Icon, items}) => (
                <article key={title} className="rounded-2xl border border-[#d0d3ea] bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-xl bg-[#f7f8fc] text-[#1a1f71] ring-1 ring-[#d0d3ea]/50">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-bold text-[#1a1f71] mb-4">{title}</h3>
                  <ul className="space-y-3">
                    {items.map((item) => (
                      <li key={item} className="flex items-center gap-2.5 text-[12px] text-[#3a3f6e]">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#f0a500] flex-shrink-0" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-[0.15em] text-[#6b6f99] px-1">Common questions I handle</h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {[
                {label: 'What is the minimum due on my credit card this month?', icon: Receipt},
                {label: 'How much did I spend on food and groceries last month?', icon: ShoppingBag},
                {label: 'What is my remaining credit limit and credit utilization?', icon: CreditCard},
                {label: 'What is my current credit score?', icon: TrendingUp},
              ].map((item) => (
                <button 
                  key={item.label} 
                  onClick={() => handleSubmit(item.label)}
                  className="rounded-xl border border-[#d0d3ea] bg-white p-4 hover:border-[#1a1f71] hover:bg-[#f7f8fc] transition-all cursor-pointer group text-left w-full"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#f7f8fc] text-[#1a1f71] group-hover:bg-white transition-colors">
                      <item.icon className="h-5 w-5" />
                    </div>
                    <span className="text-[13px] font-medium text-[#3a3f6e] group-hover:text-[#1a1f71] transition-colors">{item.label}</span>
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-xl bg-[#252b82] p-5 text-white shadow-lg border border-white/5">
            <div className="flex items-center gap-4"> 
              <div className="h-10 w-10 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                <ShieldCheck className="h-5 w-5 text-[#f0a500]" />
              </div>
              <p className="text-[12px] md:text-sm text-blue-50/90 leading-relaxed">
                All interactions are encrypted and session-bound. This assistant does not store personal data beyond the active session.
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

