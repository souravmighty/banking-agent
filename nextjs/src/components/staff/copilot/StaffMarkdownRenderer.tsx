"use client";

import React from "react";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";

export const staffAdaptiveMdComponents: Partial<Components> = {
  h1: ({ children, ...props }) => (
    <h1
      className="text-lg sm:text-xl font-extrabold mb-3 text-slate-900 dark:text-white leading-tight border-b border-slate-200 dark:border-slate-800 pb-1.5"
      {...props}
    >
      {children}
    </h1>
  ),
  h2: ({ children, ...props }) => (
    <h2
      className="text-base sm:text-lg font-bold mb-2.5 text-indigo-700 dark:text-indigo-300 leading-tight"
      {...props}
    >
      {children}
    </h2>
  ),
  h3: ({ children, ...props }) => (
    <h3
      className="text-sm sm:text-base font-bold mb-2 text-slate-800 dark:text-slate-200 leading-tight"
      {...props}
    >
      {children}
    </h3>
  ),
  h4: ({ children, ...props }) => (
    <h4
      className="text-xs sm:text-sm font-semibold mb-1.5 text-slate-700 dark:text-slate-300 leading-tight"
      {...props}
    >
      {children}
    </h4>
  ),
  p: ({ children, ...props }) => (
    <p className="mb-2 leading-relaxed text-slate-800 dark:text-slate-200 text-xs sm:text-sm last:mb-0" {...props}>
      {children}
    </p>
  ),
  ul: ({ children, ...props }) => (
    <ul
      className="list-disc list-inside mb-2.5 space-y-1 text-slate-800 dark:text-slate-200 text-xs sm:text-sm"
      {...props}
    >
      {children}
    </ul>
  ),
  ol: ({ children, ...props }) => (
    <ol
      className="list-decimal list-inside mb-2.5 space-y-1 text-slate-800 dark:text-slate-200 text-xs sm:text-sm"
      {...props}
    >
      {children}
    </ol>
  ),
  li: ({ children, ...props }) => (
    <li className="leading-relaxed text-slate-800 dark:text-slate-200" {...props}>
      {children}
    </li>
  ),
  blockquote: ({ children, ...props }) => (
    <blockquote
      className="border-l-4 border-indigo-500 pl-4 py-2 mb-2.5 bg-indigo-50 dark:bg-indigo-950/30 rounded-r text-slate-700 dark:text-slate-300 text-xs sm:text-sm italic"
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({ children, ...props }) => (
    <code
      className="bg-slate-100 dark:bg-slate-950 text-indigo-700 dark:text-indigo-300 px-1.5 py-0.5 rounded text-xs font-mono border border-slate-200 dark:border-slate-800"
      {...props}
    >
      {children}
    </code>
  ),
  pre: ({ children, ...props }) => (
    <pre
      className="bg-slate-900 text-slate-100 dark:bg-slate-950 dark:text-slate-200 p-3 rounded-xl mb-2.5 overflow-x-auto border border-slate-800 text-xs font-mono leading-relaxed w-full max-w-full min-w-0 shadow-sm"
      {...props}
    >
      {children}
    </pre>
  ),
  table: ({ children, ...props }) => (
    <div className="mb-3 overflow-x-auto w-full max-w-full rounded-xl border border-slate-200 dark:border-slate-800 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-800 shadow-sm">
      <table
        className="min-w-full border-collapse text-left text-xs text-slate-800 dark:text-slate-200 divide-y divide-slate-200 dark:divide-slate-800"
        {...props}
      >
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }) => (
    <thead className="bg-slate-100 dark:bg-slate-900/80 text-slate-700 dark:text-slate-300 font-bold uppercase text-[10px] tracking-wider" {...props}>
      {children}
    </thead>
  ),
  th: ({ children, ...props }) => (
    <th
      className="px-3 py-2.5 font-bold text-indigo-700 dark:text-indigo-300 border-b border-slate-200 dark:border-slate-800"
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ children, ...props }) => (
    <td className="px-3 py-2 text-slate-700 dark:text-slate-300 border-b border-slate-100 dark:border-slate-850/60 leading-normal" {...props}>
      {children}
    </td>
  ),
  a: ({ children, href, ...props }) => (
    <a
      className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300 underline transition-colors font-semibold"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  ),
  strong: ({ children, ...props }) => (
    <strong className="font-bold text-slate-900 dark:text-white" {...props}>
      {children}
    </strong>
  ),
  em: ({ children, ...props }) => (
    <em className="italic text-slate-700 dark:text-slate-300" {...props}>
      {children}
    </em>
  ),
};

interface StaffMarkdownRendererProps {
  content: string;
  className?: string;
}

export function StaffMarkdownRenderer({
  content,
  className = "",
}: StaffMarkdownRendererProps) {
  return (
    <div className={`markdown-content ${className} w-full max-w-full min-w-0 overflow-hidden`}>
      <ReactMarkdown components={staffAdaptiveMdComponents} remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
