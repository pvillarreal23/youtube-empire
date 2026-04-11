import { AbsoluteFill, Video, Sequence, interpolate, useCurrentFrame, Easing } from "remotion";
import { TextOverlay } from "./TextOverlay";
import type { Scene } from "../types";

type DocumentarySceneProps = {
  scene: Scene;
};

export const DocumentaryScene: React.FC<DocumentarySceneProps> = ({ scene }) => {
  const frame = useCurrentFrame();

  // Fade in
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });

  // Slow zoom (Ken Burns effect) for cinematic feel
  const scale = interpolate(frame, [0, 300], [1.0, 1.08], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      <AbsoluteFill style={{ transform: `scale(${scale})` }}>
        <Video
          src={scene.videoUrl}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          volume={0}
          muted
        />
      </AbsoluteFill>

      {/* Dark gradient overlay for text readability */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(0,0,0,0.6) 0%, transparent 40%, transparent 60%, rgba(0,0,0,0.3) 100%)",
        }}
      />

      {scene.textOverlay && <TextOverlay text={scene.textOverlay} />}
    </AbsoluteFill>
  );
};
