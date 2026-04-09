"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type ModelInfo } from "@/lib/api";

const navItems = [
  { href: "/inbox", label: "Inbox", icon: "M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" },
  { href: "/compose", label: "Compose", icon: "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" },
  { href: "/agents", label: "Agents", icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" },
  { href: "/org", label: "Org Chart", icon: "M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);

  useEffect(() => {
    api.getModelInfo().then(setModelInfo).catch(() => {});
  }, []);

  const isMythos = modelInfo?.active_preset === "mythos";

  return (
    <aside className="w-16 lg:w-56 flex flex-col border-r border-[#334155] bg-[#1e293b] shrink-0">
      <div className="p-3 lg:p-4 border-b border-[#334155]">
        <h1 className="hidden lg:block text-lg font-bold text-white tracking-tight">
          YT Empire
        </h1>
        <span className="lg:hidden text-lg font-bold text-white block text-center">YE</span>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-[#8b5cf6] text-white"
                  : "text-[#94a3b8] hover:bg-[#334155] hover:text-white"
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              <span className="hidden lg:block">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      {modelInfo && (
        <div className="px-3 py-2 border-t border-[#334155]">
          <div className="hidden lg:block">
            <div className="flex items-center gap-1.5 mb-1">
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  isMythos ? "bg-emerald-400 animate-pulse" : "bg-[#8b5cf6]"
                }`}
              />
              <span className="text-xs font-medium text-white truncate">
                {modelInfo.label}
              </span>
            </div>
            {modelInfo.extended_thinking && (
              <span className="text-[10px] text-emerald-400 font-medium">
                Extended Thinking ON
              </span>
            )}
            <div className="text-[10px] text-[#64748b] mt-0.5">
              {(modelInfo.context_window / 1000).toFixed(0)}k ctx
              {" / "}
              {(modelInfo.max_tokens / 1000).toFixed(0)}k out
            </div>
          </div>
          <div className="lg:hidden flex justify-center">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                isMythos ? "bg-emerald-400 animate-pulse" : "bg-[#8b5cf6]"
              }`}
              title={modelInfo.label}
            />
          </div>
        </div>
      )}
      <div className="p-3 border-t border-[#334155]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[#8b5cf6] flex items-center justify-center text-white text-xs font-bold">
            U
          </div>
          <span className="hidden lg:block text-sm text-[#94a3b8]">Operator</span>
        </div>
      </div>
    </aside>
  );
}
