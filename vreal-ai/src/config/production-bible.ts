export const PRODUCTION_BIBLE = {
  channel: {
    name: "@VRealAI",
    format: "faceless_ai_tools_tutorial",
    uploadCadence: "2x per week",
    targetLength: { min: 8, max: 12 }, // minutes
    publishDays: ["Tuesday", "Thursday"],
    publishTime: "14:00 EST"
  },
  brand: {
    positioning: "The faceless AI tools channel for people who want to stay sharp — fast on news, deep on analysis, practical on tutorials",
    voiceTone: "confident, direct, slightly informal — smart colleague not news anchor",
    neverSay: ["to be honest", "basically", "actually", "literally", "in this video I'm going to"],
    alwaysDo: ["open with tension not topic", "write for ears not eyes", "show before/after outputs", "cite specific numbers and dates"]
  },
  visual: {
    palette: {
      background: "#0A0F1E",
      accentPrimary: "#00D4FF",
      accentSecondary: "#FFB347",
      textPrimary: "#FFFFFF",
      textSecondary: "#C8C8C8"
    },
    thumbnailRules: {
      maxWords: 5,
      fontFamily: "Inter Black",
      faceRequired: false,
      showToolUI: true,
      contrastRatio: 7
    },
    editingRules: {
      maxUninterruptedTalkingHeadSeconds: 0, // faceless
      cutEverySeconds: { hook: 2, body: 4 },
      brollUsage: "hook and context bridges only",
      motionGraphicsRequired: true
    }
  },
  scriptTemplate: {
    sections: ["hook", "chapter1", "chapter2", "chapter3", "chapter4", "cta"],
    hookDuration: { min: 45, max: 60 }, // seconds
    hookWrittenLast: true,
    ttsFormatting: {
      maxWordsPerSentence: 20,
      pauseMarkers: ["—", "..."],
      emphasisTechnique: "sentence_length_variation"
    }
  },
  elevenlabs: {
    voiceId: "onwK4e9ZLuTAKqWW03F9", // Daniel — British, journalistic, confirmed @VRealAI voice
    model: "eleven_multilingual_v2",
    hookSettings: { stability: 0.40, similarity_boost: 0.80, style: 0.25 },
    tutorialSettings: { stability: 0.55, similarity_boost: 0.85, style: 0.10 },
    targetWPM: { min: 170, max: 220 }
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
  referral_links: {
    kling_ai: {
      code: '7B4U73LULN88',
      url: 'https://klingai.com/?ref=7B4U73LULN88',
      description: 'Kling AI — AI video generation (referral earns commission)',
      include_in_descriptions: true,
    }
  }
}
