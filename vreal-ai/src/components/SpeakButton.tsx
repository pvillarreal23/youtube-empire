"use client";
import { useSpeech } from "@/hooks/useSpeech";

interface Props {
  /** The text to read aloud. */
  text: string;
  className?: string;
}

/**
 * SpeakButton — a 🔊 / ⏹ toggle that reads text aloud using
 * the browser's free built-in Web Speech API (no API key, zero cost).
 *
 * Usage:
 *   <SpeakButton text="Hello, world!" />
 */
export default function SpeakButton({ text, className = "" }: Props) {
  const { speak, stop, isSpeaking } = useSpeech();

  const handleClick = () => {
    if (isSpeaking) {
      stop();
    } else {
      speak(text);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      title={isSpeaking ? "Stop" : "Listen"}
      className={[
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all select-none",
        isSpeaking
          ? "bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30"
          : "bg-white/5 text-white/60 border border-white/10 hover:border-white/30 hover:text-white",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span aria-hidden="true">{isSpeaking ? "⏹" : "🔊"}</span>
      <span>{isSpeaking ? "Stop" : "Listen"}</span>
    </button>
  );
}
