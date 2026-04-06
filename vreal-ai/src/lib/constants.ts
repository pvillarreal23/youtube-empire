// Agent personas mapped by ID — supports both formats (with and without -agent suffix)
const _PERSONAS: Record<string, { humanName: string; gender: "male" | "female" }> = {
  // Tier 1 — Executive
  "ceo-agent":                              { humanName: "Marcus Chen",      gender: "male"   },
  // Tier 2 — VPs
  "content-vp":                             { humanName: "Sofia Rivera",     gender: "female" },
  "operations-vp":                          { humanName: "James Okafor",     gender: "male"   },
  "analytics-vp":                           { humanName: "Priya Sharma",     gender: "female" },
  "monetization-vp":                        { humanName: "Daniel Kim",       gender: "male"   },
  // Tier 3 — Channel Managers
  "ai-and-tech-channel-manager":            { humanName: "Aisha Patel",      gender: "female" },
  "finance-and-business-channel-manager":   { humanName: "Ryan Mitchell",    gender: "male"   },
  "psychology-and-behavior-channel-manager": { humanName: "Elena Vasquez",   gender: "female" },
  // Tier 4 — Content Production
  "scriptwriter":                           { humanName: "Noah Thompson",    gender: "male"   },
  "hook-specialist":                        { humanName: "Mia Jackson",      gender: "female" },
  "storyteller":                            { humanName: "Liam O'Connor",    gender: "male"   },
  "shorts-and-clips-agent":                 { humanName: "Zara Ahmed",       gender: "female" },
  "thumbnail-designer":                     { humanName: "Kai Nakamura",     gender: "male"   },
  "video-editor":                           { humanName: "Isabella Torres",  gender: "female" },
  "seo-specialist":                         { humanName: "Ethan Park",       gender: "male"   },
  "voice-director":                         { humanName: "Carmen Reyes",     gender: "female" },
  // Tier 5 — Operations
  "project-manager":                        { humanName: "Olivia Bennett",   gender: "female" },
  "workflow-orchestrator":                   { humanName: "Amir Hassan",      gender: "male"   },
  "quality-assurance-lead":                 { humanName: "Hannah Lee",       gender: "female" },
  "reflection-council":                     { humanName: "Victor Andrei",    gender: "male"   },
  "automation-engineer":                    { humanName: "Alex Petrov",      gender: "male"   },
  // Tier 6 — Research
  "senior-researcher":                      { humanName: "Grace Nguyen",     gender: "female" },
  "trend-researcher":                       { humanName: "Leo Martinez",     gender: "male"   },
  "data-analyst":                           { humanName: "Chloe Williams",   gender: "female" },
  // Tier 7 — Monetization
  "partnership-manager":                    { humanName: "Omar Farouk",      gender: "male"   },
  "affiliate-coordinator":                  { humanName: "Natalie Brooks",   gender: "female" },
  "digital-product-manager":               { humanName: "Raj Kapoor",       gender: "male"   },
  "newsletter-strategist":                  { humanName: "Sarah Lindgren",   gender: "female" },
  // Tier 8 — Community & Social
  "community-manager":                     { humanName: "Tyler Robinson",   gender: "male"   },
  "social-media-manager":                  { humanName: "Jade Moreau",      gender: "female" },
  "secretary-agent":                        { humanName: "Emma Fischer",     gender: "female" },
  // Tier 9 — Compliance
  "compliance-officer":                    { humanName: "David Reeves",     gender: "male"   },
};

// Build lookup that supports both "content-vp" and "content-vp-agent" format
export const AGENT_PERSONAS: Record<string, { humanName: string; gender: "male" | "female" }> = {};
for (const [id, persona] of Object.entries(_PERSONAS)) {
  AGENT_PERSONAS[id] = persona;
  // Also register with -agent suffix if not already present
  if (!id.endsWith("-agent")) {
    AGENT_PERSONAS[`${id}-agent`] = persona;
  }
}

// Avatar files use {id}-agent.jpg except when id already ends with "-agent"
export const AVATAR_OVERRIDES: Record<string, string> = {
  'quality-assurance-lead': '/avatars/qa-lead-agent.jpg',
  'automation-engineer': '/avatars/workflow-orchestrator-agent.jpg',
  'voice-director': '/avatars/scriptwriter-agent.jpg',
};

export function getAgentAvatar(agentId: string, avatarUrl?: string): string {
  if (avatarUrl) return avatarUrl;
  if (AVATAR_OVERRIDES[agentId]) return AVATAR_OVERRIDES[agentId];
  if (agentId.endsWith('-agent')) return `/avatars/${agentId}.jpg`;
  return `/avatars/${agentId}-agent.jpg`;
}

export function getHumanName(agentId: string): string {
  return AGENT_PERSONAS[agentId]?.humanName || "";
}

// 9-Tier V-Real AI system
export type Tier = "T1" | "T2" | "T3" | "T4" | "T5" | "T6" | "T7" | "T8" | "T9";

export const TIER_LABELS: Record<Tier, string> = {
  "T1": "Executive", "T2": "VP", "T3": "Channel Mgr", "T4": "Production",
  "T5": "Operations", "T6": "Research", "T7": "Monetization", "T8": "Community", "T9": "Compliance",
};

export const TIER_STYLES: Record<Tier, { bg: string; border: string; text: string; badge: string; ring: string }> = {
  "T1": { bg: "bg-yellow-500/5",  border: "border-yellow-500/30", text: "text-yellow-400",  badge: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30", ring: "ring-yellow-500/60" },
  "T2": { bg: "bg-purple-500/5",  border: "border-purple-500/30", text: "text-purple-400",  badge: "bg-purple-500/20 text-purple-300 border-purple-500/30", ring: "ring-purple-500/60" },
  "T3": { bg: "bg-blue-500/5",    border: "border-blue-500/30",   text: "text-blue-400",    badge: "bg-blue-500/20 text-blue-300 border-blue-500/30",     ring: "ring-blue-500/60" },
  "T4": { bg: "bg-cyan-500/5",    border: "border-cyan-500/30",   text: "text-cyan-400",    badge: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",     ring: "ring-cyan-500/60" },
  "T5": { bg: "bg-amber-500/5",   border: "border-amber-500/30",  text: "text-amber-400",   badge: "bg-amber-500/20 text-amber-300 border-amber-500/30",   ring: "ring-amber-500/60" },
  "T6": { bg: "bg-emerald-500/5", border: "border-emerald-500/30",text: "text-emerald-400", badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30", ring: "ring-emerald-500/60" },
  "T7": { bg: "bg-red-500/5",     border: "border-red-500/30",    text: "text-red-400",     badge: "bg-red-500/20 text-red-300 border-red-500/30",         ring: "ring-red-500/60" },
  "T8": { bg: "bg-pink-500/5",    border: "border-pink-500/30",   text: "text-pink-400",    badge: "bg-pink-500/20 text-pink-300 border-pink-500/30",       ring: "ring-pink-500/60" },
  "T9": { bg: "bg-slate-500/5",   border: "border-slate-500/30",  text: "text-slate-400",   badge: "bg-slate-500/20 text-slate-300 border-slate-500/30",     ring: "ring-slate-500/60" },
};

// Map agent IDs to tiers based on the V-Real AI 9-tier structure
export const AGENT_TIER_MAP: Record<string, number> = {
  "ceo-agent": 1,
  "content-vp": 2, "operations-vp": 2, "analytics-vp": 2, "monetization-vp": 2,
  "ai-and-tech-channel-manager": 3, "finance-and-business-channel-manager": 3, "psychology-and-behavior-channel-manager": 3,
  "scriptwriter": 4, "hook-specialist": 4, "storyteller": 4, "shorts-and-clips-agent": 4,
  "thumbnail-designer": 4, "video-editor": 4, "seo-specialist": 4, "voice-director": 4,
  "project-manager": 5, "workflow-orchestrator": 5, "quality-assurance-lead": 5, "reflection-council": 5, "automation-engineer": 5,
  "senior-researcher": 6, "trend-researcher": 6, "data-analyst": 6,
  "partnership-manager": 7, "affiliate-coordinator": 7, "digital-product-manager": 7, "newsletter-strategist": 7,
  "community-manager": 8, "social-media-manager": 8, "secretary-agent": 8,
  "compliance-officer": 9,
};

export function getAgentTier(agentId: string): Tier {
  const normalized = agentId.replace(/-agent$/, "");
  const t = AGENT_TIER_MAP[agentId] || AGENT_TIER_MAP[normalized] || 5;
  return `T${t}` as Tier;
}

export const DEPT_COLORS: Record<string, { dot: string; label: string }> = {
  executive:    { dot: "bg-yellow-400", label: "Executive" },
  content:      { dot: "bg-blue-400",   label: "Content" },
  operations:   { dot: "bg-amber-400",  label: "Operations" },
  analytics:    { dot: "bg-emerald-400",label: "Analytics" },
  monetization: { dot: "bg-red-400",    label: "Monetization" },
  admin:        { dot: "bg-slate-400",  label: "Admin" },
  general:      { dot: "bg-gray-400",   label: "General" },
};
