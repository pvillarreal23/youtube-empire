import { Composition, Folder } from "remotion";
import { Episode } from "./Episode";
import { Short } from "./Short";
import type { EpisodeProps, ShortProps } from "./types";

const FPS = 30;

/**
 * Default props for preview in Remotion Studio.
 * In production, these are overridden with real data from the pipeline.
 */
const defaultEpisodeProps: EpisodeProps = {
  title: "Wake Up",
  voiceoverUrl: "",
  scenes: [],
  captions: [],
  durationInSeconds: 480, // 8 minutes default
};

const defaultShortProps: ShortProps = {
  title: "AI is replacing your job",
  voiceoverUrl: "",
  videoUrl: "",
  captions: [],
  durationInSeconds: 45,
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="V-Real AI">
        {/* Long-form episode — 16:9 landscape */}
        <Composition
          id="VRealEpisode"
          component={Episode}
          durationInFrames={defaultEpisodeProps.durationInSeconds * FPS}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={defaultEpisodeProps}
        />

        {/* YouTube Short — 9:16 vertical */}
        <Composition
          id="VRealShort"
          component={Short}
          durationInFrames={defaultShortProps.durationInSeconds * FPS}
          fps={FPS}
          width={1080}
          height={1920}
          defaultProps={defaultShortProps}
        />
      </Folder>
    </>
  );
};
