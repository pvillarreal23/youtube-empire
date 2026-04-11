import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";

type TitleCardProps = {
  title: string;
  subtitle?: string;
};

export const TitleCard: React.FC<TitleCardProps> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();

  const titleOpacity = interpolate(frame, [0, 30], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });

  const titleY = interpolate(frame, [0, 30], [40, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });

  const subtitleOpacity = interpolate(frame, [20, 50], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const lineWidth = interpolate(frame, [10, 40], [0, 300], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0f172a",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          fontSize: 72,
          fontWeight: 700,
          color: "#ffffff",
          fontFamily: "Inter, sans-serif",
          textAlign: "center",
        }}
      >
        {title}
      </div>

      <div
        style={{
          width: lineWidth,
          height: 3,
          backgroundColor: "#8b5cf6",
          marginTop: 20,
          marginBottom: 20,
        }}
      />

      {subtitle && (
        <div
          style={{
            opacity: subtitleOpacity,
            fontSize: 28,
            color: "#94a3b8",
            fontFamily: "Inter, sans-serif",
          }}
        >
          {subtitle}
        </div>
      )}
    </AbsoluteFill>
  );
};
