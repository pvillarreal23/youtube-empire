"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, OrgTree } from "@/lib/api";
import { getInitials } from "@/lib/utils";
import { getHumanName, getAgentTier, TIER_STYLES } from "@/lib/constants";
import { ChevronRight } from "lucide-react";

interface TreeNode {
  id: string;
  name: string;
  role: string;
  department: string;
  color: string;
  children: TreeNode[];
}

function buildTree(org: OrgTree): TreeNode[] {
  const nodeMap: Record<string, TreeNode> = {};
  const childSet = new Set<string>();

  org.nodes.forEach((n) => {
    nodeMap[n.id] = { ...n, children: [] };
  });

  org.edges.forEach((e) => {
    if (nodeMap[e.source] && nodeMap[e.target]) {
      nodeMap[e.source].children.push(nodeMap[e.target]);
      childSet.add(e.target);
    }
  });

  return Object.values(nodeMap).filter((n) => !childSet.has(n.id));
}

function OrgNodeComponent({ node, depth = 0 }: { node: TreeNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children.length > 0;
  const tier = getAgentTier(node.id);
  const tierStyle = TIER_STYLES[tier];
  const humanName = getHumanName(node.id);

  return (
    <div className={depth > 0 ? "ml-6 border-l border-white/5 pl-4" : ""}>
      <div className="flex items-center gap-3 py-2 group">
        {hasChildren ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-5 h-5 flex items-center justify-center text-white/30 hover:text-white"
          >
            <ChevronRight className={`w-3 h-3 transition-transform ${expanded ? "rotate-90" : ""}`} />
          </button>
        ) : (
          <div className="w-5" />
        )}
        <Link
          href={`/agents/${node.id}`}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity"
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
            style={{ backgroundColor: node.color }}
          >
            {getInitials(node.name)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-white">{humanName || node.name}</span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded border ${tierStyle.badge}`}>{tier}</span>
            </div>
            <div className="text-xs text-white/30">{node.role}</div>
          </div>
        </Link>
        {hasChildren && (
          <span className="text-[10px] text-white/20 ml-1">({node.children.length})</span>
        )}
      </div>
      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <OrgNodeComponent key={child.id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function OrgChartPage() {
  const [org, setOrg] = useState<OrgTree | null>(null);

  useEffect(() => {
    api.getOrgTree().then(setOrg);
  }, []);

  if (!org) return <div className="flex items-center justify-center h-full text-white/30">Loading...</div>;

  const tree = buildTree(org);

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-white/5">
        <h2 className="text-xl font-semibold text-white">Organization Chart</h2>
        <p className="text-sm text-white/30 mt-1">{org.nodes.length} agents across the empire</p>
      </header>
      <div className="flex-1 overflow-y-auto p-6">
        {tree.map((root) => (
          <OrgNodeComponent key={root.id} node={root} />
        ))}
      </div>
    </div>
  );
}
