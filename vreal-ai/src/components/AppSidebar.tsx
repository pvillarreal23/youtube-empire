"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Inbox, PenSquare, Users, Network, LayoutDashboard, ChevronLeft, ChevronRight, DollarSign } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, color: "text-blue-400" },
  { href: "/inbox", label: "Inbox", icon: Inbox, color: "text-cyan-400" },
  { href: "/compose", label: "Compose", icon: PenSquare, color: "text-purple-400" },
  { href: "/agents", label: "Agents", icon: Users, color: "text-green-400" },
  { href: "/org", label: "Org Chart", icon: Network, color: "text-amber-400" },
  { href: "/costs", label: "Cost Control", icon: DollarSign, color: "text-[#00D4FF]" },
];

export default function AppSidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(true);

  return (
    <aside className={`${open ? "w-56" : "w-16"} shrink-0 border-r border-white/5 bg-black/40 backdrop-blur-xl flex flex-col transition-all duration-200`}>
      {/* Logo */}
      <div className="p-4 border-b border-white/5 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shrink-0">
          <LayoutDashboard className="w-4 h-4 text-white" />
        </div>
        {open && <span className="text-sm font-bold text-white">V-Real AI</span>}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                isActive
                  ? "bg-white/10 text-white"
                  : "text-white/40 hover:text-white/70 hover:bg-white/5"
              }`}
            >
              <item.icon className={`w-5 h-5 shrink-0 ${isActive ? item.color : ""}`} />
              {open && <span className="font-medium text-xs">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Pedro */}
      <div className="p-3 border-t border-white/5">
        <div className="flex items-center gap-2.5">
          <img src="/avatars/pedro.jpg" className="w-8 h-8 rounded-full object-cover ring-2 ring-purple-500/50" alt="" />
          {open && (
            <div>
              <p className="text-xs font-semibold text-white">Pedro</p>
              <p className="text-[9px] text-white/30">Empire Operator</p>
            </div>
          )}
        </div>
      </div>

      {/* Collapse toggle */}
      <button onClick={() => setOpen(!open)} className="p-2 border-t border-white/5 text-white/20 hover:text-white/50">
        {open ? <ChevronLeft className="w-4 h-4 mx-auto" /> : <ChevronRight className="w-4 h-4 mx-auto" />}
      </button>
    </aside>
  );
}
