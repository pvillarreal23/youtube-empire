export const dynamic = 'force-dynamic';

import { promises as fs } from 'fs';
import path from 'path';

interface MemoryReadRequest {
  type?: 'video' | 'performance' | 'decision' | 'insight' | 'experiment';
  key?: string;
  tags?: string[];
  limit?: number;
}

interface MemoryEntry {
  entry_id: string;
  timestamp: string;
  type: string;
  key: string;
  tags: string[];
  data: Record<string, unknown>;
}

interface MemoryReadResponse {
  entries: MemoryEntry[];
  total: number;
  files_searched: string[];
}

const DATA_DIR = path.join(process.cwd(), 'data');

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<MemoryReadRequest>;
    const limit = body.limit ?? 50;

    const types = body.type ? [body.type] : ['video', 'performance', 'decision', 'insight', 'experiment'];
    const filesSearched: string[] = [];
    const allEntries: MemoryEntry[] = [];

    await fs.mkdir(DATA_DIR, { recursive: true });

    for (const type of types) {
      const filename = `memory_${type}.jsonl`;
      const filepath = path.join(DATA_DIR, filename);
      filesSearched.push(filename);

      try {
        const content = await fs.readFile(filepath, 'utf-8');
        const lines = content.trim().split('\n').filter(Boolean);
        for (const line of lines) {
          try {
            const entry = JSON.parse(line) as MemoryEntry;
            // Filter by key if specified
            if (body.key && !entry.key.includes(body.key)) continue;
            // Filter by tags if specified
            if (body.tags && body.tags.length > 0) {
              const hasTag = body.tags.some((t) => entry.tags.includes(t));
              if (!hasTag) continue;
            }
            allEntries.push(entry);
          } catch {
            // Skip malformed lines
          }
        }
      } catch {
        // File doesn't exist yet, skip
      }
    }

    // Sort by timestamp descending, apply limit
    allEntries.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
    const entries = allEntries.slice(0, limit);

    return Response.json({ entries, total: allEntries.length, files_searched: filesSearched } satisfies MemoryReadResponse);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message }, { status: 500 });
  }
}
