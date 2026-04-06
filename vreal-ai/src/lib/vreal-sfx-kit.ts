export const VREAL_SFX_KIT = {
  transition: "Dark digital whoosh transition with electric crackle and deep bass tail, cinematic sci-fi, 1 second",
  impact: "Deep cinematic boom impact with reverb tail, dramatic low frequency hit, dark cinematic, 1.5 seconds",
  riser: "Dark cinematic tension riser building steadily in pitch and intensity, electric hum, 2 seconds",
  cut: "Sharp digital glitch cut sound, brief electronic snap, dark sci-fi, 0.5 seconds",
  ping: "Subtle electric ping notification sound, clean and modern, brief, 0.5 seconds"
} as const

export type SfxType = keyof typeof VREAL_SFX_KIT
