import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";

type TextOverlayProps = {
  text: string;
  position?: "bottom" | "center" | "top";
};

export const TextOverlay: React.FC<TextOverlayProps> = ({
  text,
  position = "bottom",
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15, 15, 15], [0, 1, 1, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });

  const positionStyle: React.CSSProperties =
    position === "bottom"
      ? { bottom: 120, left: 0, right: 0 }
      : position === "top"
        ? { top: 60, left: 0, right: 0 }
        : { top: "50%", left: 0, right: 0, transform: "translateY(-50%)" };

  return (
    <div
      style={{
        position: "absolute",
        ...positionStyle,
        display: "flex",
        justifyContent: "center",
        opacity,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.7)",
          padding: "12px 32px",
          borderRadius: 8,
          borderLeft: "3px solid #8b5cf6",
        }}
      >
        <span
          style={{
            color: "#ffffff",
            fontSize: 32,
            fontWeight: 600,
            fontFamily: "Inter, sans-serif",
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};
