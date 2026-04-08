export const PRODUCTION_BIBLE = {
  channel: {
    name: "@VRealAI",
    format: "faceless_documentary_ai_storytelling",
    uploadCadence: "2x per week",
    targetLength: { min: 8, max: 12 }, // minutes
    publishDays: ["Tuesday", "Thursday"],
    publishTime: "14:00 EST",
    contentMix: { breakdowns: 0.45, playbooks: 0.40, stories: 0.15 }
  },
  brand: {
    positioning: "AI-powered documentary channel exploring how artificial intelligence is reshaping work, business, and daily life. For marketing professionals and solopreneurs adapting to AI disruption.",
    voiceTone: "BBC/Netflix documentary — cinematic, rhythmic, intimate. Smart friend sharing what they discovered, not news anchor or hype-man",
    tagline: "You're not paranoid. You're observant.",
    signatureLines: [
      "No one sent an announcement. No one rang a bell. The rules just changed.",
      "They no longer require mastery of execution. They require taste.",
      "You're not paranoid. You're observant.",
      "This is V-Real AI."
    ],
    neverSay: ["to be honest", "basically", "actually", "literally", "in this video I'm going to", "let's dive in", "without further ado", "game-changer", "revolutionize", "comprehensive guide", "delve", "utilize", "robust"],
    alwaysDo: ["open with tension not topic", "write for ears not eyes", "tell stories not lectures", "cite specific numbers and dates", "name what viewers feel — never tell them what to do", "use contractions always"]
  },
  visual: {
    palette: {
      background: "#0A0F1E",
      accentPrimary: "#00D4FF",    // Electric blue — AI moments, data, digital
      accentSecondary: "#FFB347",  // Warm amber — human moments, hope, warmth
      textPrimary: "#FFFFFF",
      textSecondary: "#C8C8C8"
    },
    animationStyle: {
      approach: "cinematic_stock_plus_motion_graphics", // Option A — for launch
      footageHierarchy: [
        "1. Kling AI custom — unique scenes stock can't provide",
        "2. Cinematic stock footage — Artgrid, Storyblocks (real footage, never photos)",
        "3. Screen recordings with animated annotations — for tool demos only",
        "4. Custom motion graphics and data visualizations",
        "5. Animated maps, timelines, diagrams",
        "6. Ken Burns on high-quality photos — sparingly",
        "7. Static stock photos — LAST RESORT, always with overlay animation"
      ],
      colorGrade: "Cool shadows, warm highlights, teal-orange split tone",
      motionStyle: "Smooth, cinematic — slow zooms, gentle orbits, no jerky cuts",
      aiMoments: "Blue/purple palette, particles, digital textures",
      humanMoments: "Warm amber tones, natural lighting, grounded",
      transitions: "Light leaks for soft, hard cuts for impact, whip pans for energy",
      maxStaticShot: 2 // seconds — NEVER exceed this in faceless content
    },
    thumbnailRules: {
      maxWords: 5,
      fontFamily: "Inter Black",
      faceRequired: false,
      showToolUI: true,
      contrastRatio: 7,
      testAtMobileSize: "120px wide",
      concepts: 3, // always generate 3 before picking
      textCompletesTitle: true // thumbnail text adds to title, never repeats it
    },
    editingRules: {
      maxUninterruptedTalkingHeadSeconds: 0, // faceless — no talking head ever
      maxStaticShotSeconds: 2, // the "Never Boring" rule
      cutEverySeconds: { hook: 2, body: 4 },
      patternInterruptInterval: { min: 15, max: 20 }, // seconds
      majorVisualShiftInterval: { min: 45, max: 60 }, // seconds
      motionGraphicsRequired: true,
      audioLayers: {
        voice: "-14 to -16 LUFS",
        music: "-25 to -30 LUFS, ducking to -35 under voice",
        sfx: "strategic — transitions, emphasis, reveals",
        ambient: "subtle room/atmosphere when needed"
      }
    }
  },
  scriptTemplate: {
    structure: ["hook", "act1_setup", "act2_journey", "act3_transformation", "closing"],
    targetWordCount: { min: 1100, max: 1300 }, // ~8-9 min at 150-160 WPM
    hookDuration: { min: 15, max: 30 }, // seconds — tighter than before
    storyRequired: true, // every script must have a character and arc
    animationCues: {
      required: true,
      tags: ["[ANIM:]", "[TEXT-ON-SCREEN:]", "[KLING-AI:]", "[MUSIC:]", "[SFX:]", "[PAUSE]", "[DATA-VIZ:]", "[TRANSITION:]"],
      frequencyPerParagraph: 1 // minimum 1 visual cue every 2-3 sentences
    },
    ttsFormatting: {
      maxWordsPerSentence: 15, // tighter for AI voice
      pauseMarkers: ["—", "...", "[PAUSE 0.5s]", "[PAUSE 1s]"],
      emphasisTechnique: "sentence_length_variation",
      avoidInAIVoice: ["tongue-twisters", "parenthetical asides", "sarcasm", "lists > 3 items read aloud"]
    },
    voicePrinciples: {
      rhythm: "Short lines. Strategic pauses. One breath or silence.",
      tone: "Documentary, not hustle. BBC/Netflix, not Gary Vee.",
      specificity: "Concrete beats abstract. Specific numbers, specific verbs.",
      earnedClaims: "A specific claim only works if the narrative built to it.",
      intimacy: "Meet the viewer where they are. Never declare at them.",
      identity: "Name what they feel. Never tell them what to do."
    }
  },
  elevenlabs: {
    voiceId: "CjK4w2V6sbgFJY05zTGt", // Pedro V-Real v2 — production voice clone, LOCKED for @VRealAI
    voiceName: "V-Real AI Voice (Julian Clone)",
    model: "eleven_multilingual_v2",
    // LOCKED settings — do not change without full team sign-off
    settings: { stability: 0.65, similarity_boost: 0.75, style: 0.00, speaker_boost: false },
    // Pacing varies by section, but these are the global targets
    targetWPM: { documentary: { min: 130, max: 160 }, energetic: { min: 160, max: 175 } }
  },
  seo: {
    titleFormulas: [
      "[TOOL]: [SURPRISING RESULT]",
      "The [TOOL] Secret Nobody Is Talking About",
      "I Tested [TOOL] For [TIME] — Here's What Actually Happened",
      "[OLD WAY] vs [TOOL]: The Real Difference",
      "Why Everyone Is Using [TOOL] Wrong"
    ],
    titleMaxChars: 60,
    primaryKeywordPosition: "first 40 characters",
    requiredInVideo: "speak primary keyword in first 30 seconds",
    chaptersRequired: true,
    uploadSchedule: "Tuesday + Thursday 2PM EST"
  },
  competitors: {
    studyClosely: ["@fireship", "@mreflow", "@aiexplained", "@skillleapai"],
    steal: {
      fireship: "dark minimal thumbnail, 100-second intro format, cut pacing",
      mattWolfe: "weekly roundup format, curator positioning",
      twoMinutePapers: "before/after output comparison structure",
      skillLeapAI: "evergreen tutorial SEO strategy"
    }
  },
  assetSourcing: {
    video: {
      primary: ["Kling AI (custom)", "Artgrid", "Storyblocks"],
      secondary: ["Pexels Video"],
      neverUse: ["watermarked footage", "resolution below 1080p", "generic laptop-typing stock"]
    },
    music: {
      primary: "Epidemic Sound",
      style: "Cinematic electronic — Hans Zimmer meets Tycho. Builds tension, resolves with hope.",
      rules: ["No lyrics", "Change track/intensity at major topic shifts", "Use silence deliberately"]
    },
    motionGraphics: {
      primary: ["Envato Elements", "Motion Array"],
      templates: ["Lower thirds", "Data viz", "Kinetic text", "Transitions"]
    },
    thumbnails: {
      imagery: "Midjourney for custom, Canva for layout",
      style: "Dark background, bold text, high emotional contrast"
    }
  },
  referral_links: {
    kling_ai: {
      code: '7B4U73LULN88',
      url: 'https://klingai.com/?ref=7B4U73LULN88',
      description: 'Kling AI — AI video generation (referral earns commission)',
      include_in_descriptions: true,
    }
  }
}
