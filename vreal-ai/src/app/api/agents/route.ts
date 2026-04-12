import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';

interface Agent {
  id: string;
  name: string;
  role: string;
  tier: number;
  department: string;
  avatar: string;
  reports_to?: string;
  direct_reports?: string[];
  collaborates_with?: string[];
  primary_tools?: string[];
  personality_trait?: string;
  special_skill?: string;
  weakness_to_watch?: string;
  learning_focus?: string;
}

// Avatar files use {id}-agent.jpg except when id already ends with "-agent"
// Special cases for non-standard filenames
const AVATAR_OVERRIDES: Record<string, string> = {
  'quality-assurance-lead': '/avatars/qa-lead-agent.jpg',
  'automation-engineer': '/avatars/workflow-orchestrator-agent.jpg', // fallback
  'voice-director': '/avatars/scriptwriter-agent.jpg', // fallback
};

function getAvatarPath(id: string): string {
  if (AVATAR_OVERRIDES[id]) return AVATAR_OVERRIDES[id];
  if (id.endsWith('-agent')) return `/avatars/${id}.jpg`;
  return `/avatars/${id}-agent.jpg`;
}

async function parseAgentFiles(): Promise<Agent[]> {
  const agents: Agent[] = [];

  try {
    const agentsDir = path.join(process.cwd(), 'agents');

    // Get all tier directories
    const tierDirs = await fs.readdir(agentsDir);

    for (const tierDir of tierDirs) {
      if (!tierDir.startsWith('tier-')) continue;

      const tierPath = path.join(agentsDir, tierDir);
      const stat = await fs.stat(tierPath);
      if (!stat.isDirectory()) continue;

      // Get all agent files in this tier
      const files = await fs.readdir(tierPath);

      for (const file of files) {
        if (!file.endsWith('.md')) continue;

        const filePath = path.join(tierPath, file);
        const content = await fs.readFile(filePath, 'utf-8');

        // Parse YAML frontmatter
        const match = content.match(/^---\n([\s\S]*?)\n---/);
        if (!match) continue;

        const frontmatter = match[1];
        const agentId = file.replace('.md', '');
        const agent: Agent = {
          id: agentId,
          name: '',
          role: '',
          tier: 0,
          department: '',
          avatar: getAvatarPath(agentId),
        };

        // Parse YAML properties
        const lines = frontmatter.split('\n');
        for (const line of lines) {
          const [key, ...valueParts] = line.split(':');
          const value = valueParts.join(':').trim();

          if (key === 'name') {
            agent.name = value;
          } else if (key === 'role') {
            agent.role = value;
          } else if (key === 'tier') {
            agent.tier = parseInt(value, 10);
          } else if (key === 'department') {
            agent.department = value;
          } else if (key === 'reports_to') {
            agent.reports_to = value === 'None' ? undefined : value;
          } else if (key === 'direct_reports') {
            const match = value.match(/\[(.*?)\]/);
            if (match) {
              agent.direct_reports = match[1].split(',').map(s => s.trim());
            }
          } else if (key === 'collaborates_with') {
            const match = value.match(/\[(.*?)\]/);
            if (match) {
              agent.collaborates_with = match[1].split(',').map(s => s.trim());
            }
          } else if (key === 'primary_tools') {
            const match = value.match(/\[(.*?)\]/);
            if (match) {
              agent.primary_tools = match[1].split(',').map(s => s.trim());
            }
          } else if (key === 'personality_trait') {
            agent.personality_trait = value;
          } else if (key === 'special_skill') {
            agent.special_skill = value;
          } else if (key === 'weakness_to_watch') {
            agent.weakness_to_watch = value;
          } else if (key === 'learning_focus') {
            agent.learning_focus = value;
          }
        }

        if (agent.name && agent.role) {
          agents.push(agent);
        }
      }
    }
  } catch (error) {
    console.error('Error parsing agents:', error);
  }

  // Sort by tier
  agents.sort((a, b) => a.tier - b.tier || a.name.localeCompare(b.name));
  return agents;
}

export async function GET() {
  try {
    const agents = await parseAgentFiles();
    return NextResponse.json(agents);
  } catch (error) {
    console.error('Error in agents API:', error);
    return NextResponse.json([]);
  }
}
