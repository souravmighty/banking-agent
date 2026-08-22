"use client";

import React from "react";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { StaffVegaChart, parseAndCleanVegaSpec } from "./StaffVegaChart";

function isVegaLiteSpec(content: string): boolean {
  try {
    const parsed = parseAndCleanVegaSpec(content);
    return (
      typeof parsed === "object" &&
      parsed !== null &&
      (Boolean(typeof parsed.$schema === "string" && parsed.$schema.includes("vega-lite")) ||
        (Boolean(parsed.mark || parsed.layer) && Boolean(parsed.data || parsed.encoding)))
    );
  } catch {
    return false;
  }
}

export const staffAdaptiveMdComponents: Partial<Components> = {
  h1: ({ children, ...props }) => (
    <h1
      className="text-lg sm:text-xl font-extrabold mb-3 text-slate-900 leading-tight border-b border-slate-200 pb-1.5"
      {...props}
    >
      {children}
    </h1>
  ),
  h2: ({ children, ...props }) => (
    <h2
      className="text-base sm:text-lg font-bold mb-2.5 text-indigo-700 leading-tight"
      {...props}
    >
      {children}
    </h2>
  ),
  h3: ({ children, ...props }) => (
    <h3
      className="text-sm sm:text-base font-bold mb-2 text-slate-800 leading-tight"
      {...props}
    >
      {children}
    </h3>
  ),
  h4: ({ children, ...props }) => (
    <h4
      className="text-xs sm:text-sm font-semibold mb-1.5 text-slate-700 leading-tight"
      {...props}
    >
      {children}
    </h4>
  ),
  p: ({ children, ...props }) => (
    <p className="mb-2 leading-relaxed text-slate-800 text-xs sm:text-sm last:mb-0" {...props}>
      {children}
    </p>
  ),
  ul: ({ children, ...props }) => (
    <ul
      className="list-disc list-inside mb-2.5 space-y-1 text-slate-800 text-xs sm:text-sm"
      {...props}
    >
      {children}
    </ul>
  ),
  ol: ({ children, ...props }) => (
    <ol
      className="list-decimal list-inside mb-2.5 space-y-1 text-slate-800 text-xs sm:text-sm"
      {...props}
    >
      {children}
    </ol>
  ),
  li: ({ children, ...props }) => (
    <li className="leading-relaxed text-slate-800" {...props}>
      {children}
    </li>
  ),
  blockquote: ({ children, ...props }) => (
    <blockquote
      className="border-l-4 border-indigo-500 pl-4 py-2 mb-2.5 bg-indigo-50/80 rounded-r text-slate-700 text-xs sm:text-sm italic"
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({ className, children, ...props }) => {
    const codeString = String(children).replace(/\n$/, "");
    const match = /language-(\w+)/.exec(className || "");
    const language = match ? match[1].toLowerCase() : "";

    if (
      language === "vega-lite" ||
      language === "vegalite" ||
      language === "vega" ||
      (language === "json" && isVegaLiteSpec(codeString)) ||
      isVegaLiteSpec(codeString)
    ) {
      return <StaffVegaChart spec={codeString} />;
    }

    const isMultiline = codeString.includes("\n");
    if (!className && !isMultiline) {
      return (
        <code
          className="bg-slate-100 text-indigo-700 px-1.5 py-0.5 rounded text-xs font-mono border border-slate-200/80"
          {...props}
        >
          {children}
        </code>
      );
    }

    return (
      <code className={`${className || ""} text-xs font-mono`} {...props}>
        {children}
      </code>
    );
  },
  pre: ({ children, ...props }) => {
    // If child is already a chart or contains chart, unwrap completely without pre box styling
    const childArray = React.Children.toArray(children);
    const hasChart = childArray.some((child) => {
      if (!React.isValidElement(child)) return false;
      const childProps = child.props as {
        className?: string;
        children?: React.ReactNode;
      };
      const className = childProps?.className || "";
      const match = /language-(\w+)/.exec(className);
      const language = match ? match[1].toLowerCase() : "";
      const codeString = String(childProps?.children || "").replace(/\n$/, "");

      return (
        language === "vega-lite" ||
        language === "vegalite" ||
        language === "vega" ||
        (language === "json" && isVegaLiteSpec(codeString)) ||
        isVegaLiteSpec(codeString) ||
        child.type === StaffVegaChart
      );
    });

    if (hasChart) {
      return <div className="w-full my-1">{children}</div>;
    }

    return (
      <pre
        className="bg-slate-50 text-slate-800 p-3 sm:p-4 rounded-xl mb-3 overflow-x-auto border border-slate-200 text-xs font-mono leading-relaxed w-full max-w-full min-w-0 shadow-xs"
        {...props}
      >
        {children}
      </pre>
    );
  },
  table: ({ children, ...props }) => (
    <div className="mb-3 overflow-x-auto w-full max-w-full rounded-xl border border-slate-200 scrollbar-thin scrollbar-thumb-slate-300 shadow-xs">
      <table
        className="min-w-full border-collapse text-left text-xs text-slate-800 divide-y divide-slate-200"
        {...props}
      >
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }) => (
    <thead className="bg-slate-100/90 text-slate-700 font-bold uppercase text-[10px] tracking-wider" {...props}>
      {children}
    </thead>
  ),
  th: ({ children, ...props }) => (
    <th
      className="px-3 py-2.5 font-bold text-indigo-700 border-b border-slate-200"
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ children, ...props }) => (
    <td className="px-3 py-2 text-slate-700 border-b border-slate-100 leading-normal" {...props}>
      {children}
    </td>
  ),
  a: ({ children, href, ...props }) => (
    <a
      className="text-indigo-600 hover:text-indigo-500 underline transition-colors font-semibold"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  ),
  strong: ({ children, ...props }) => (
    <strong className="font-bold text-slate-900" {...props}>
      {children}
    </strong>
  ),
  em: ({ children, ...props }) => (
    <em className="italic text-slate-700" {...props}>
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
