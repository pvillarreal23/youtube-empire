import { useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
import type { CaptionPage } from "../types";

type CaptionsProps = {
  pages: CaptionPage[];
};

export const Captions: React.FC<CaptionsProps> = ({ pages }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeMs = (frame / fps) * 1000;

  // Find the active caption page
  const activePage = pages.find(
    (p) => currentTimeMs >= p.startMs && currentTimeMs < p.endMs
  );

  if (!activePage) return null;

  // Calculate fade in
  const pageStartFrame = (activePage.startMs / 1000) * fps;
  const localFrame = frame - pageStartFrame;
  const opacity = interpolate(localFrame, [0, 8], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.8)",
          padding: "10px 24px",
          borderRadius: 6,
          maxWidth: "80%",
        }}
      >
        <span
          style={{
            color: "#ffffff",
            fontSize: 28,
            fontWeight: 500,
            fontFamily: "Inter, sans-serif",
            lineHeight: 1.4,
            whiteSpace: "pre-wrap",
            textAlign: "center",
          }}
        >
          {activePage.tokens.map((token, i) => {
            const isActive =
              currentTimeMs >= token.startMs && currentTimeMs < token.endMs;
            return (
              <span
                key={i}
                style={{
                  color: isActive ? "#8b5cf6" : "#ffffff",
                  fontWeight: isActive ? 700 : 500,
                  transition: "color 0.1s",
                }}
              >
                {token.text}{" "}
              </span>
            );
          })}
        </span>
      </div>
    </div>
  );
};
