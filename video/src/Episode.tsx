import {
  AbsoluteFill,
  Audio,
  Sequence,
  useVideoConfig,
} from "remotion";
import { TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { linearTiming } from "@remotion/transitions/timing";
import { TitleCard } from "./components/TitleCard";
import { DocumentaryScene } from "./components/DocumentaryScene";
import { Captions } from "./components/Captions";
import type { EpisodeProps } from "./types";

const TRANSITION_FRAMES = 15;

export const Episode: React.FC<EpisodeProps> = ({
  title,
  voiceoverUrl,
  scenes,
  captions,
}) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
      {/* Title card — first 4 seconds */}
      <Sequence durationInFrames={4 * fps}>
        <TitleCard title={title} subtitle="V-Real AI" />
      </Sequence>

      {/* Scene footage with transitions */}
      <Sequence from={4 * fps}>
        <TransitionSeries>
          {scenes.map((scene, i) => {
            const sceneDurationFrames = Math.round(scene.duration * fps);
            return [
              <TransitionSeries.Sequence
                key={`scene-${scene.id}`}
                durationInFrames={sceneDurationFrames}
              >
                <DocumentaryScene scene={scene} />
              </TransitionSeries.Sequence>,
              i < scenes.length - 1 ? (
                <TransitionSeries.Transition
                  key={`transition-${scene.id}`}
                  presentation={fade()}
                  timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
                />
              ) : null,
            ];
          })}
        </TransitionSeries>
      </Sequence>

      {/* Voiceover audio — starts after title card */}
      <Sequence from={4 * fps}>
        <Audio
          src={voiceoverUrl}
          volume={(f) => {
            // Fade in over first 15 frames
            if (f < 15) return f / 15;
            return 1;
          }}
        />
      </Sequence>

      {/* Captions overlay — always on top, starts after title card */}
      <Sequence from={4 * fps}>
        <Captions pages={captions} />
      </Sequence>

      {/* Watermark */}
      <div
        style={{
          position: "absolute",
          bottom: 20,
          right: 24,
          color: "rgba(255,255,255,0.3)",
          fontSize: 14,
          fontFamily: "Inter, sans-serif",
          fontWeight: 600,
        }}
      >
        V-Real AI
      </div>
    </AbsoluteFill>
  );
};
