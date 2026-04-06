import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const BrandedIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoScale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 100 },
    from: 0,
    to: 1,
  });

  const textOpacity = interpolate(frame, [20, 45], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const taglineOpacity = interpolate(frame, [40, 65], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const glowIntensity = interpolate(frame, [0, 45, 90], [0, 1, 0.6], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0A0F1E",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Inter', 'SF Pro Display', sans-serif",
      }}
    >
      {/* Glow background circle */}
      <div
        style={{
          position: "absolute",
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: `radial-gradient(circle, rgba(0, 212, 255, ${glowIntensity * 0.12}) 0%, transparent 70%)`,
        }}
      />

      {/* Logo mark */}
      <div
        style={{
          transform: `scale(${logoScale})`,
          marginBottom: 40,
        }}
      >
        <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
          <polygon
            points="50,5 95,95 5,95"
            stroke="#00D4FF"
            strokeWidth="4"
            fill="none"
            style={{
              filter: `drop-shadow(0 0 ${glowIntensity * 20}px #00D4FF)`,
            }}
          />
          <circle
            cx="50"
            cy="60"
            r="12"
            fill="#00D4FF"
            style={{
              filter: `drop-shadow(0 0 ${glowIntensity * 15}px #00D4FF)`,
            }}
          />
        </svg>
      </div>

      {/* Brand name */}
      <div
        style={{
          opacity: textOpacity,
          fontSize: 80,
          fontWeight: 800,
          letterSpacing: "-2px",
          color: "#FFFFFF",
          textTransform: "uppercase",
        }}
      >
        The{" "}
        <span
          style={{
            color: "#00D4FF",
            textShadow: `0 0 ${glowIntensity * 40}px rgba(0, 212, 255, 0.8)`,
          }}
        >
          Edge
        </span>{" "}
        AI
      </div>

      {/* Tagline */}
      <div
        style={{
          opacity: taglineOpacity,
          fontSize: 28,
          fontWeight: 300,
          letterSpacing: "6px",
          color: "rgba(255,255,255,0.55)",
          textTransform: "uppercase",
          marginTop: 16,
        }}
      >
        Build the Future
      </div>

      {/* Bottom accent line */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          width: interpolate(frame, [50, 80], [0, 400], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          height: 2,
          background:
            "linear-gradient(90deg, transparent, #00D4FF, transparent)",
          opacity: glowIntensity,
        }}
      />
    </AbsoluteFill>
  );
};
