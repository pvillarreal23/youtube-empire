export const dynamic = 'force-dynamic';

import { promises as fs } from 'fs';
import path from 'path';

interface MemoryLogRequest {
  type: 'video' | 'performance' | 'decision' | 'insight' | 'experiment';
  key: string;
  data: Record<string, unknown>;
  tags?: string[];
}

interface MemoryLogResponse {
  logged: boolean;
  entry_id: string;
  timestamp: string;
  file: string;
}

const DATA_DIR = path.join(process.cwd(), 'data');

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<MemoryLogRequest>;

    if (!body.type?.trim() || !body.key?.trim() || !body.data) {
      return Response.json({ error: 'Missing required fields: type, key, data' }, { status: 400 });
    }

    await fs.mkdir(DATA_DIR, { recursive: true });

    const filename = `memory_${body.type}.jsonl`;
    const filepath = path.join(DATA_DIR, filename);

    const entry = {
      entry_id: `${body.type}_${Date.now()}`,
      timestamp: new Date().toISOString(),
      type: body.type,
      key: body.key,
      tags: body.tags ?? [],
      data: body.data,
    };

    await fs.appendFile(filepath, JSON.stringify(entry) + '\n', 'utf-8');

    return Response.json({
      logged: true,
      entry_id: entry.entry_id,
      timestamp: entry.timestamp,
      file: filename,
    } satisfies MemoryLogResponse);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message }, { status: 500 });
  }
}
