import { NextRequest, NextResponse } from 'next/server';
import { VREAL_SFX_KIT, type SfxType } from '@/lib/vreal-sfx-kit';

interface WordTimestamp {
  word: string;
  start_ms: number;
  end_ms: number;
}

interface VisualScene {
  scene_number: number;
  description: string;
  visual_tag: string;
  script_cue: string;
}

interface TimelineEntry {
  scene_number: number;
  visual_tag: string;
  script_cue: string;
  start_ms: number;
  end_ms: number;
  sfx_type: SfxType;
  sfx_prompt: string;
}

function determineSfxType(visualTag: string): SfxType {
  const lowerTag = visualTag.toLowerCase();

  if (
    lowerTag.includes('shatter') ||
    lowerTag.includes('slam') ||
    lowerTag.includes('walls') ||
    lowerTag.includes('gate') ||
    lowerTag.includes('fall') ||
    lowerTag.includes('crash')
  ) {
    return 'impact';
  }

  if (lowerTag.includes('riser') || lowerTag.includes('tension') || lowerTag.includes('build')) {
    return 'riser';
  }

  if (lowerTag.includes('subscribe') || lowerTag.includes('cta') || lowerTag.includes('ping') || lowerTag.includes('button')) {
    return 'ping';
  }

  if (lowerTag.includes('cut') || lowerTag.includes('glitch') || lowerTag.includes('snap')) {
    return 'cut';
  }

  return 'transition';
}

function findScriptCueTimestamp(scriptCue: string, wordTimestamps: WordTimestamp[]): { start_ms: number; end_ms: number } | null {
  const cueLower = scriptCue.toLowerCase().trim();
  const cueWords = cueLower.split(/\s+/);

  if (cueWords.length === 0) {
    return null;
  }

  const firstCueWord = cueWords[0];

  for (let i = 0; i < wordTimestamps.length; i++) {
    if (wordTimestamps[i].word.toLowerCase() === firstCueWord) {
      // Find where this sequence ends
      let j = i;
      while (j < Math.min(i + cueWords.length, wordTimestamps.length)) {
        j++;
      }
      const endIdx = j - 1;

      return {
        start_ms: wordTimestamps[i].start_ms,
        end_ms: wordTimestamps[endIdx]?.end_ms ?? wordTimestamps[i].end_ms,
      };
    }
  }

  return null;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json() as {
      word_timestamps: WordTimestamp[];
      visual_scenes: VisualScene[];
    };

    const { word_timestamps, visual_scenes } = body;

    if (!word_timestamps || !Array.isArray(word_timestamps)) {
      return NextResponse.json({ error: 'word_timestamps is required and must be an array' }, { status: 400 });
    }

    if (!visual_scenes || !Array.isArray(visual_scenes)) {
      return NextResponse.json({ error: 'visual_scenes is required and must be an array' }, { status: 400 });
    }

    const timeline: TimelineEntry[] = visual_scenes.map((scene) => {
      const sfx_type = determineSfxType(scene.visual_tag);
      const sfx_prompt = VREAL_SFX_KIT[sfx_type];

      const timing = findScriptCueTimestamp(scene.script_cue, word_timestamps);
      const start_ms = timing?.start_ms ?? 0;
      const end_ms = timing?.end_ms ?? 0;

      return {
        scene_number: scene.scene_number,
        visual_tag: scene.visual_tag,
        script_cue: scene.script_cue,
        start_ms,
        end_ms,
        sfx_type,
        sfx_prompt,
      };
    });

    return NextResponse.json({ timeline });
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
