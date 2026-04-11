import {
  AbsoluteFill,
  Audio,
  Video,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";
import { Captions } from "./components/Captions";
import type { ShortProps } from "./types";

/**
 * YouTube Short / TikTok / Reels format
 * 1080x1920 (9:16 vertical), 30fps, max 60 seconds
 */
export const Short: React.FC<ShortProps> = ({
  title,
  voiceoverUrl,
  videoUrl,
  captions,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Title flash at the start
  const titleOpacity = interpolate(frame, [0, 10, 60, 75], [0, 1, 1, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });

  // Slow zoom
  const scale = interpolate(frame, [0, 600], [1.0, 1.12], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
      {/* Background video */}
      <AbsoluteFill style={{ transform: `scale(${scale})` }}>
        <Video
          src={videoUrl}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          volume={0}
          muted
        />
      </AbsoluteFill>

      {/* Dark gradient */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 30%, transparent 70%, rgba(0,0,0,0.5) 100%)",
        }}
      />

      {/* Title overlay */}
      <div
        style={{
          position: "absolute",
          top: "15%",
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(139, 92, 246, 0.9)",
            padding: "12px 28px",
            borderRadius: 8,
          }}
        >
          <span
            style={{
              color: "#ffffff",
              fontSize: 36,
              fontWeight: 700,
              fontFamily: "Inter, sans-serif",
              textAlign: "center",
            }}
          >
            {title}
          </span>
        </div>
      </div>

      {/* Voiceover */}
      <Audio src={voiceoverUrl} />

      {/* Captions — positioned for vertical format */}
      <Captions pages={captions} />

      {/* Watermark */}
      <div
        style={{
          position: "absolute",
          top: 40,
          left: 24,
          color: "rgba(255,255,255,0.5)",
          fontSize: 18,
          fontFamily: "Inter, sans-serif",
          fontWeight: 700,
        }}
      >
        @VRealAI
      </div>
    </AbsoluteFill>
  );
};
