"use client";

import React, { useEffect, useRef, useState } from "react";
import { BarChart3, AlertCircle, RefreshCw } from "lucide-react";
import type { Result, VisualizationSpec } from "vega-embed";

interface StaffVegaChartProps {
  spec: string | Record<string, unknown>;
  className?: string;
}

const D3_NUMBER_FORMAT_REGEX =
  /^(?:(.)?([<>=^]))?([+\-( ])?([$#])?(0)?(\d+)?(,)?(\.\d+)?(~)?([a-z%])?$/i;

function isLikelyD3TimeFormat(formatStr: string): boolean {
  return /%[a-zA-Z%]/.test(formatStr);
}

function sanitizeFormatValue(
  formatVal: unknown
): { cleanFormat?: string; labelExprPrefix?: string; formatType?: string } {
  if (typeof formatVal !== "string") {
    return {};
  }

  const trimmed = formatVal.trim();
  if (!trimmed) {
    return {};
  }

  // Valid standard d3 number format
  if (D3_NUMBER_FORMAT_REGEX.test(trimmed)) {
    return { cleanFormat: trimmed };
  }

  // Valid d3 time format (e.g. "%Y-%m-%d", "%b %Y")
  if (isLikelyD3TimeFormat(trimmed)) {
    return { cleanFormat: trimmed, formatType: "time" };
  }

  // Check for common currency prefix (e.g. "₹~s", "₹,.0f", "₹s", "€~s", "Rs. ~s", "$~s")
  const prefixMatch = trimmed.match(
    /^([₹€£¥$]|Rs\.?|INR|USD|EUR|GBP)\s*(.*)$/i
  );
  if (prefixMatch) {
    const symbol = prefixMatch[1].trim();
    const remaining = prefixMatch[2].trim();

    if (remaining && D3_NUMBER_FORMAT_REGEX.test(remaining)) {
      return {
        cleanFormat: remaining,
        labelExprPrefix: symbol === "$" ? "" : symbol,
      };
    } else if (!remaining) {
      return {
        cleanFormat: undefined,
        labelExprPrefix: symbol === "$" ? "" : symbol,
      };
    }
  }

  // Check for suffix currency (e.g. "~s ₹" or ",.0f INR")
  const suffixMatch = trimmed.match(
    /^(.*?)\s*([₹€£¥]|Rs\.?|INR|USD|EUR|GBP)$/i
  );
  if (suffixMatch) {
    const remaining = suffixMatch[1].trim();
    if (remaining && D3_NUMBER_FORMAT_REGEX.test(remaining)) {
      return {
        cleanFormat: remaining,
      };
    }
  }

  // Check if a valid d3 specifier is embedded inside
  const embeddedMatch = trimmed.match(
    /([+\-( ])?([$#])?(0)?(\d+)?(,)?(\.\d+)?(~)?([a-z%])/i
  );
  if (embeddedMatch) {
    const candidate = embeddedMatch[0];
    if (D3_NUMBER_FORMAT_REGEX.test(candidate)) {
      return { cleanFormat: candidate };
    }
  }

  return {};
}

export function sanitizeVegaSpecFormats(
  specObj: Record<string, unknown>
): Record<string, unknown> {
  if (!specObj || typeof specObj !== "object") return specObj;

  const clone = JSON.parse(JSON.stringify(specObj));

  function walk(node: unknown, parentKey = ""): void {
    if (!node || typeof node !== "object") return;

    if (Array.isArray(node)) {
      for (const item of node) {
        walk(item, parentKey);
      }
      return;
    }

    const obj = node as Record<string, unknown>;

    // Handle axis objects
    if (
      parentKey === "axis" ||
      ("orient" in obj && ("title" in obj || "labels" in obj || "format" in obj))
    ) {
      if (typeof obj.format === "string") {
        const { cleanFormat, labelExprPrefix, formatType } = sanitizeFormatValue(
          obj.format
        );
        if (cleanFormat) {
          obj.format = cleanFormat;
        } else {
          delete obj.format;
        }

        if (formatType && !obj.formatType) {
          obj.formatType = formatType;
        }

        if (labelExprPrefix && !obj.labelExpr) {
          obj.labelExpr = `'${labelExprPrefix}' + datum.label`;
        }
      }
    } else if (typeof obj.format === "string") {
      const { cleanFormat, formatType } = sanitizeFormatValue(obj.format);
      if (cleanFormat) {
        obj.format = cleanFormat;
      } else {
        delete obj.format;
      }
      if (formatType && !obj.formatType) {
        obj.formatType = formatType;
      }
    }

    for (const [key, val] of Object.entries(obj)) {
      if (val && typeof val === "object") {
        walk(val, key);
      }
    }
  }

  walk(clone);
  return clone;
}

export function parseAndCleanVegaSpec(
  specInput: string | Record<string, unknown>
): Record<string, unknown> {
  let parsed: Record<string, unknown>;

  if (typeof specInput === "object" && specInput !== null) {
    parsed = specInput;
    return sanitizeVegaSpecFormats(parsed);
  }

  let text = String(specInput).trim();

  // Strip markdown code fences if wrapped
  if (text.startsWith("```")) {
    text = text
      .replace(/^```[a-zA-Z0-9_-]*\s*\n?/, "")
      .replace(/\n?```\s*$/, "")
      .trim();
  }

  // Attempt 1: Standard JSON.parse
  try {
    const direct = JSON.parse(text);
    if (typeof direct === "object" && direct !== null) {
      return sanitizeVegaSpecFormats(direct as Record<string, unknown>);
    }
    if (typeof direct === "string") {
      const nested = JSON.parse(direct);
      if (typeof nested === "object" && nested !== null) {
        return sanitizeVegaSpecFormats(nested as Record<string, unknown>);
      }
    }
  } catch {
    // Continue
  }

  // Extract from outer braces { ... } if surrounded by commentary
  const firstBrace = text.indexOf("{");
  const lastBrace = text.lastIndexOf("}");
  if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
    text = text.slice(firstBrace, lastBrace + 1);
  }

  // Attempt 2: After brace extraction
  try {
    const parsedObj = JSON.parse(text);
    if (typeof parsedObj === "object" && parsedObj !== null) {
      return sanitizeVegaSpecFormats(parsedObj as Record<string, unknown>);
    }
  } catch {
    // Continue
  }

  // Attempt 3: Repair literal escaped newlines/tabs and quotes (e.g. `},\n {`)
  try {
    const unescaped = text
      .replace(/\\n/g, "\n")
      .replace(/\\r/g, "\r")
      .replace(/\\t/g, "\t")
      .replace(/\\"/g, '"')
      .replace(/,\s*([}\]])/g, "$1");
    const parsedObj = JSON.parse(unescaped);
    if (typeof parsedObj === "object" && parsedObj !== null) {
      return sanitizeVegaSpecFormats(parsedObj as Record<string, unknown>);
    }
  } catch {
    // Continue
  }

  // Attempt 4: Replace literal \n and \r with spaces/newlines and strip trailing commas
  try {
    const sanitized = text
      .replace(/\\n/g, "\n")
      .replace(/\\r/g, "")
      .replace(/\\t/g, " ")
      .replace(/,\s*([}\]])/g, "$1");
    const parsedObj = JSON.parse(sanitized);
    if (typeof parsedObj === "object" && parsedObj !== null) {
      return sanitizeVegaSpecFormats(parsedObj as Record<string, unknown>);
    }
  } catch {
    // Continue
  }

  // Attempt 5: Handle Python-style booleans/nulls and single quotes
  try {
    let pythonFixed = text
      .replace(/\\n/g, "\n")
      .replace(/\\r/g, "")
      .replace(/\bNone\b/g, "null")
      .replace(/\bTrue\b/g, "true")
      .replace(/\bFalse\b/g, "false")
      .replace(/,\s*([}\]])/g, "$1");

    if (pythonFixed.includes("'")) {
      pythonFixed = pythonFixed.replace(/'([^'\\]*(?:\\.[^'\\]*)*)'/g, '"$1"');
    }
    const parsedObj = JSON.parse(pythonFixed);
    if (typeof parsedObj === "object" && parsedObj !== null) {
      return sanitizeVegaSpecFormats(parsedObj as Record<string, unknown>);
    }
  } catch {
    // Fallback to direct parse error
  }

  const rawParsed = JSON.parse(text);
  return sanitizeVegaSpecFormats(rawParsed);
}

export function StaffVegaChart({ spec, className = "" }: StaffVegaChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    let embedResult: Result | null = null;

    async function renderChart() {
      if (!containerRef.current) return;
      setIsLoading(true);
      setError(null);

      try {
        const parsedSpec = parseAndCleanVegaSpec(spec);

        // Modern, polished light theme configuration matching ABC Bank styling
        const themedSpec: VisualizationSpec = {
          $schema: "https://vega.github.io/schema/vega-lite/v5.json",
          width: "container",
          height: 300,
          autosize: { type: "fit", contains: "padding" },
          ...parsedSpec,
          background: "transparent",
          config: {
            font: "var(--font-inter), system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
            background: "transparent",
            view: {
              stroke: "transparent",
              fill: "transparent",
            },
            range: {
              category: [
                "#4f46e5", // Indigo (Primary)
                "#0284c7", // Sky blue
                "#059669", // Emerald green
                "#d97706", // Amber / Warm gold
                "#7c3aed", // Violet / Purple
                "#e11d48", // Rose / Red
                "#0d9488", // Teal
                "#ea580c", // Orange
                "#6366f1", // Iris
                "#2563eb", // Royal blue
              ],
              diverging: ["#ef4444", "#f59e0b", "#10b981"],
              heatmap: ["#eef2ff", "#6366f1", "#312e81"],
            },
            axis: {
              labelFont: "var(--font-inter), system-ui, sans-serif",
              labelFontSize: 11,
              labelFontWeight: 500,
              labelColor: "#64748b",
              labelPadding: 6,
              titleFont: "var(--font-inter), system-ui, sans-serif",
              titleFontSize: 11.5,
              titleFontWeight: 600,
              titleColor: "#334155",
              titlePadding: 10,
              gridColor: "#f1f5f9",
              gridWidth: 1,
              gridDash: [3, 3],
              domainColor: "#cbd5e1",
              domainWidth: 1,
              tickColor: "#cbd5e1",
              tickSize: 4,
            },
            axisX: {
              grid: false,
            },
            axisY: {
              grid: true,
              gridColor: "#f1f5f9",
            },
            legend: {
              labelFont: "var(--font-inter), system-ui, sans-serif",
              labelFontSize: 11,
              labelFontWeight: 500,
              labelColor: "#475569",
              labelOffset: 6,
              titleFont: "var(--font-inter), system-ui, sans-serif",
              titleFontSize: 11.5,
              titleFontWeight: 600,
              titleColor: "#1e293b",
              titlePadding: 6,
              symbolType: "circle",
              symbolSize: 75,
              orient: "right",
              offset: 14,
            },
            title: {
              font: "var(--font-inter), system-ui, sans-serif",
              fontSize: 14,
              fontWeight: 700,
              color: "#0f172a",
              subtitleFont: "var(--font-inter), system-ui, sans-serif",
              subtitleFontSize: 11.5,
              subtitleFontWeight: 400,
              subtitleColor: "#64748b",
              subtitlePadding: 4,
              anchor: "start",
              offset: 14,
            },
            bar: {
              cornerRadiusTopLeft: 6,
              cornerRadiusTopRight: 6,
            },
            line: {
              strokeWidth: 2.5,
            },
            point: {
              size: 55,
              filled: true,
            },
            arc: {
              innerRadius: 50,
              cornerRadius: 4,
            },
            ...((parsedSpec.config as Record<string, unknown>) || {}),
          },
        } as unknown as VisualizationSpec;

        const vegaEmbed = (await import("vega-embed")).default;

        if (!isMounted || !containerRef.current) return;

        // Clear previous chart
        containerRef.current.innerHTML = "";

        const result = await vegaEmbed(containerRef.current, themedSpec, {
          actions: {
            export: true,
            source: false,
            compiled: false,
            editor: false,
          },
          renderer: "svg",
        });

        embedResult = result;
        if (isMounted) {
          setIsLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg);
          setIsLoading(false);
        }
      }
    }

    renderChart();

    return () => {
      isMounted = false;
      if (embedResult?.view && typeof embedResult.view.finalize === "function") {
        embedResult.view.finalize();
      }
    };
  }, [spec]);

  return (
    <div
      className={`my-4 rounded-2xl border border-slate-200/90 bg-white p-4 sm:p-5 shadow-sm hover:shadow-md transition-all duration-200 w-full overflow-hidden ${className}`}
    >
      {/* Chart Header Bar */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 text-xs font-semibold text-slate-700">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-xs">
            <BarChart3 className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold text-slate-800">
            Interactive Visual Breakdown
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isLoading ? (
            <div className="flex items-center gap-1.5 text-[11px] font-medium text-indigo-600 bg-indigo-50/70 border border-indigo-100 px-2 py-0.5 rounded-md animate-pulse">
              <RefreshCw className="w-3 h-3 animate-spin" />
              <span>Rendering chart...</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-500 bg-slate-50 border border-slate-200/60 px-2 py-0.5 rounded-md">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live BI Analytics</span>
            </div>
          )}
        </div>
      </div>

      {error ? (
        <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 text-xs">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-amber-600" />
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-amber-800">Chart Specification Notice</p>
            <p className="text-[11px] text-amber-700 mt-0.5">{error}</p>
            <pre className="mt-2 p-2.5 bg-white border border-amber-200 text-slate-700 rounded-lg text-[10px] font-mono overflow-x-auto max-h-36">
              {typeof spec === "string" ? spec : JSON.stringify(spec, null, 2)}
            </pre>
          </div>
        </div>
      ) : (
        <div className="w-full flex justify-center items-center min-h-[280px] overflow-x-auto py-1">
          <div
            ref={containerRef}
            className="w-full flex justify-center items-center [&_.vega-embed]:flex [&_.vega-embed]:justify-center [&_.vega-embed]:w-full"
          />
        </div>
      )}
    </div>
  );
}
