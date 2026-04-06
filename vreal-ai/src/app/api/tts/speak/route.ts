// This route has been replaced by the client-side Web Speech API.
// See src/hooks/useSpeech.ts and src/components/SpeakButton.tsx.
// The browser's built-in speechSynthesis requires no API key and has zero cost.
export async function POST(): Promise<Response> {
  return new Response(
    JSON.stringify({ error: "This endpoint is deprecated. Use the browser Web Speech API instead." }),
    { status: 410, headers: { "Content-Type": "application/json" } },
  );
}
