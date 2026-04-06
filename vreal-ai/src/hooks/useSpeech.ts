"use client";
import { useState, useCallback, useEffect, useRef } from "react";

/**
 * useSpeech — wraps the browser's built-in Web Speech API.
 *
 * Returns:
 *   speak(text)  — reads text aloud (cancels any in-progress speech first)
 *   stop()       — cancels current speech
 *   isSpeaking   — true while the browser is speaking
 *
 * Voice preference: "Google US English" → any Google EN voice → any EN voice
 * Rate: 0.95  Pitch: 1.0  Volume: 1.0
 */
export function useSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Cancel speech when the component using this hook unmounts
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined") {
        window.speechSynthesis?.cancel();
      }
    };
  }, []);

  /** Pick the best available English voice. */
  const getVoice = (): SpeechSynthesisVoice | null => {
    const voices = window.speechSynthesis.getVoices();
    return (
      voices.find((v) => v.name === "Google US English") ??
      voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          v.name.toLowerCase().includes("google"),
      ) ??
      voices.find((v) => v.lang.startsWith("en")) ??
      null
    );
  };

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;

    // Cancel anything already playing
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Voices may not be loaded yet on first call; try again after voiceschanged
    const voice = getVoice();
    if (voice) {
      utterance.voice = voice;
    } else {
      const onVoicesChanged = () => {
        const v = getVoice();
        if (v) utterance.voice = v;
        window.speechSynthesis.removeEventListener(
          "voiceschanged",
          onVoicesChanged,
        );
      };
      window.speechSynthesis.addEventListener(
        "voiceschanged",
        onVoicesChanged,
      );
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, []);

  const stop = useCallback(() => {
    if (typeof window === "undefined") return;
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  }, []);

  return { speak, stop, isSpeaking };
}
