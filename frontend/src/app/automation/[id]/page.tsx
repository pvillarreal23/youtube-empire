"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, type WorkflowRun } from "@/lib/api";
import { timeAgo } from "@/lib/utils";

const STATUS_STYLES: Record<string, string> = {
  running: "bg-blue-500/20 text-blue-400",
  completed: "bg-emerald-500/20 text-emerald-400",
  failed: "bg-red-500/20 text-red-400",
};

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [copied, setCopied] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);

  useEffect(() => {
    params.then((p) => setRunId(p.id));
  }, [params]);

  useEffect(() => {
    if (!runId) return;
    api.getRunDetail(runId).then(setRun).catch(() => {});
  }, [runId]);

  // Poll while running
  useEffect(() => {
    if (!runId || !run || run.status !== "running") return;
    const interval = setInterval(() => {
      api.getRunDetail(runId).then(setRun).catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [runId, run]);

  const handleCopy = () => {
    if (run?.output) {
      navigator.clipboard.writeText(run.output);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!run) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0f172a]">
        <p className="text-[#64748b]">Loading...</p>
      </div>
    );
  }

  const workflowName = run.workflow_id
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="h-full flex flex-col bg-[#0f172a]">
      {/* Header */}
      <div className="p-4 lg:p-6 border-b border-[#334155]">
        <div className="flex items-center gap-3 mb-2">
          <Link
            href="/automation"
            className="text-[#64748b] hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
          </Link>
          <h1 className="text-xl font-bold text-white">{workflowName}</h1>
          <span className={`px-2.5 py-1 rounded text-xs font-semibold ${STATUS_STYLES[run.status] || ""}`}>
            {run.status}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-[#64748b]">
          {run.channel && (
            <span className="bg-[#334155] rounded px-2 py-0.5">
              {run.channel}
            </span>
          )}
          <span>Started {timeAgo(run.created_at)}</span>
          {run.completed_at && <span>Completed {timeAgo(run.completed_at)}</span>}
        </div>
      </div>

      {/* Output */}
      <div className="flex-1 overflow-hidden flex flex-col p-4 lg:p-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-white">Output</h2>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-[#334155] text-[#94a3b8] hover:text-white transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
            </svg>
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <div className="flex-1 rounded-xl border border-[#334155] bg-[#1e293b] overflow-auto">
          {run.status === "running" && !run.output ? (
            <div className="flex items-center justify-center h-full gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              <span className="text-sm text-[#64748b]">Agent is working...</span>
            </div>
          ) : (
            <pre className="p-4 lg:p-6 font-mono text-xs text-[#94a3b8] whitespace-pre-wrap leading-relaxed">
              {run.output || "No output yet."}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
