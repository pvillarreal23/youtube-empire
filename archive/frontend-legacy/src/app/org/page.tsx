"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, OrgTree } from "@/lib/api";
import { getInitials } from "@/lib/utils";

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

  // Root nodes are those not in childSet
  return Object.values(nodeMap).filter((n) => !childSet.has(n.id));
}

function OrgNode({ node, depth = 0 }: { node: TreeNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children.length > 0;

  return (
    <div className={depth > 0 ? "ml-6 border-l border-[#334155] pl-4" : ""}>
      <div className="flex items-center gap-3 py-2 group">
        {hasChildren && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-5 h-5 flex items-center justify-center text-[#64748b] hover:text-white"
          >
            <svg
              className={`w-3 h-3 transition-transform ${expanded ? "rotate-90" : ""}`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        )}
        {!hasChildren && <div className="w-5" />}
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
            <div className="text-sm font-medium text-white">{node.name}</div>
            <div className="text-xs text-[#64748b]">{node.role}</div>
          </div>
        </Link>
        {hasChildren && (
          <span className="text-[10px] text-[#64748b] ml-1">({node.children.length})</span>
        )}
      </div>
      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <OrgNode key={child.id} node={child} depth={depth + 1} />
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

  if (!org) return <div className="flex items-center justify-center h-full text-[#64748b]">Loading...</div>;

  const tree = buildTree(org);

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-[#334155]">
        <h2 className="text-xl font-semibold text-white">Organization Chart</h2>
        <p className="text-sm text-[#64748b] mt-1">{org.nodes.length} agents across the empire</p>
      </header>
      <div className="flex-1 overflow-y-auto p-6">
        {tree.map((root) => (
          <OrgNode key={root.id} node={root} />
        ))}
      </div>
    </div>
  );
}
