import { Composition } from "remotion";
import { BrandedIntro } from "./BrandedIntro";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BrandedIntro"
        component={BrandedIntro}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
