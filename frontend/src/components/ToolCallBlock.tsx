"use client";

import { useState } from "react";
import { ToolCallInfo } from "@/lib/api";

const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
  completed: { color: "#10b981", bg: "#10b98120", label: "Completed" },
  executing: { color: "#f59e0b", bg: "#f59e0b20", label: "Executing" },
  pending: { color: "#6366f1", bg: "#6366f120", label: "Pending" },
  failed: { color: "#ef4444", bg: "#ef444420", label: "Failed" },
};

function formatValue(value: unknown, indent = 0): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    if (value.length === 0) return "[]";
    return JSON.stringify(value, null, 2);
  }
  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

export default function ToolCallBlock({ toolCall }: { toolCall: ToolCallInfo }) {
  const [expanded, setExpanded] = useState(false);
  const config = statusConfig[toolCall.status] || statusConfig.pending;

  return (
    <div
      className="mt-2 rounded-md border overflow-hidden"
      style={{ borderColor: config.color + "40" }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs transition-colors hover:bg-[#ffffff08]"
        style={{ backgroundColor: config.bg }}
      >
        <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke={config.color} strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span className="font-medium text-[#e2e8f0]">
          {toolCall.tool_name}
        </span>
        <span
          className="px-1.5 py-0.5 rounded text-[10px] font-medium"
          style={{ backgroundColor: config.bg, color: config.color, border: `1px solid ${config.color}40` }}
        >
          {config.label}
        </span>
        <svg
          className={`w-3 h-3 ml-auto text-[#64748b] transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="px-3 py-2 space-y-2 border-t" style={{ borderColor: config.color + "20", backgroundColor: "#0f172a" }}>
          {toolCall.input_data && Object.keys(toolCall.input_data).length > 0 && (
            <div>
              <div className="text-[10px] font-semibold text-[#64748b] uppercase tracking-wider mb-1">Input</div>
              <pre className="text-[11px] text-[#94a3b8] bg-[#1e293b] rounded px-2 py-1.5 overflow-x-auto whitespace-pre-wrap">
                {formatValue(toolCall.input_data)}
              </pre>
            </div>
          )}
          {toolCall.output_data && (
            <div>
              <div className="text-[10px] font-semibold text-[#64748b] uppercase tracking-wider mb-1">Output</div>
              <pre className="text-[11px] text-[#94a3b8] bg-[#1e293b] rounded px-2 py-1.5 overflow-x-auto whitespace-pre-wrap">
                {formatValue(toolCall.output_data)}
              </pre>
            </div>
          )}
          {toolCall.error_message && (
            <div>
              <div className="text-[10px] font-semibold text-[#ef4444] uppercase tracking-wider mb-1">Error</div>
              <pre className="text-[11px] text-[#fca5a5] bg-[#1e293b] rounded px-2 py-1.5 overflow-x-auto whitespace-pre-wrap">
                {toolCall.error_message}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
