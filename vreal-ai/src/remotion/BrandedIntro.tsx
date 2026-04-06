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

      {/* Logo mark — V-shaped icon representing V-Real */}
      <div
        style={{
          transform: `scale(${logoScale})`,
          marginBottom: 40,
        }}
      >
        <svg width="120" height="100" viewBox="0 0 120 100" fill="none">
          {/* V shape */}
          <path
            d="M10,10 L60,90 L110,10"
            stroke="#00D4FF"
            strokeWidth="5"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            style={{
              filter: `drop-shadow(0 0 ${glowIntensity * 20}px #00D4FF)`,
            }}
          />
          {/* Dot accent at the V base */}
          <circle
            cx="60"
            cy="90"
            r="6"
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
        <span
          style={{
            color: "#00D4FF",
            textShadow: `0 0 ${glowIntensity * 40}px rgba(0, 212, 255, 0.8)`,
          }}
        >
          V-Real
        </span>{" "}
        AI
      </div>

      {/* Tagline */}
      <div
        style={{
          opacity: taglineOpacity,
          fontSize: 24,
          fontWeight: 300,
          letterSpacing: "4px",
          color: "rgba(255,255,255,0.55)",
          marginTop: 16,
          fontStyle: "italic",
        }}
      >
        You're not paranoid. You're observant.
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
