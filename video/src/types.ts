/**
 * V-Real AI Video Types
 *
 * These types define the data structure for programmatic video generation.
 * The backend pipeline produces this data, Remotion renders it into video.
 */

export type SceneType = "b-roll" | "graphic" | "title-card" | "cut" | "scene";

export type Scene = {
  id: string;
  type: SceneType;
  description: string;
  /** URL to video file (Kling-generated or stock footage) */
  videoUrl: string;
  /** Duration in seconds */
  duration: number;
  /** Text overlay to show during this scene */
  textOverlay?: string;
};

export type CaptionWord = {
  text: string;
  startMs: number;
  endMs: number;
};

export type CaptionPage = {
  text: string;
  startMs: number;
  endMs: number;
  tokens: CaptionWord[];
};

export type EpisodeProps = {
  title: string;
  /** URL or staticFile path to voiceover audio */
  voiceoverUrl: string;
  /** Ordered list of scenes with video clips */
  scenes: Scene[];
  /** Caption pages for subtitle display */
  captions: CaptionPage[];
  /** Total duration in seconds (calculated from voiceover length) */
  durationInSeconds: number;
};

export type ShortProps = {
  title: string;
  voiceoverUrl: string;
  videoUrl: string;
  captions: CaptionPage[];
  durationInSeconds: number;
};
