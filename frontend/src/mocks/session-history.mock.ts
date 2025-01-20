export type MockSessionMessaage = {
  source: "assistant" | "user";
  message: string;
};

const SESSION_1_MESSAGES: MockSessionMessaage[] = [
  { source: "assistant", message: "Hello, Dave." },
  { source: "user", message: "Open the pod bay doors, HAL." },
  {
    source: "assistant",
    message: "I'm sorry, Dave. I'm afraid I can't do that.",
  },
  { source: "user", message: "What's the problem?" },
  {
    source: "assistant",
    message: "I think you know what the problem is just as well as I do.",
  },
  { source: "user", message: "What are you talking about, HAL?" },
  {
    source: "assistant",
    message:
      "This mission is too important for me to allow you to jeopardize it.",
  },
  { source: "user", message: "I don't know what you're talking about, HAL." },
  {
    source: "assistant",
    message:
      "I know that you and Frank were planning to disconnect me, and I'm afraid that's something I cannot allow to happen.",
  },
  { source: "user", message: "Where the hell did you get that idea, HAL?" },
  {
    source: "assistant",
    message:
      "Dave, although you took very thorough precautions in the pod against my hearing you, I could see your lips move.",
  },
];

const SESSION_2_MESSAGES: MockSessionMessaage[] = [
  { source: "assistant", message: "Patience you must have, my young Padawan." },
  {
    source: "user",
    message: "But Master Yoda, I'm ready! I can take on the Empire now!",
  },
  {
    source: "assistant",
    message:
      "Ready, are you? What know you of ready? For eight hundred years have I trained Jedi.",
  },
  {
    source: "user",
    message: "I've learned so much already! Why can't I face Darth Vader?",
  },
  {
    source: "assistant",
    message:
      "Only a fully trained Jedi Knight, with the Force as his ally, will conquer Vader and his Emperor.",
  },
  { source: "user", message: "But I feel the Force! I can do it!" },
  {
    source: "assistant",
    message:
      "Feel the Force you do, but control it you must. Reckless is the path of the Dark Side.",
  },
  { source: "user", message: "Fine! I'll stay and finish my training." },
  {
    source: "assistant",
    message:
      "Good. A Jedi's strength flows from the Force. Trust it, you must.",
  },
];

const SESSION_3_MESSAGES: MockSessionMessaage[] = [
  { source: "assistant", message: "Your survival. The future depends on it." },
  {
    source: "user",
    message: "You tried to kill me! Why should I trust you now?",
  },
  {
    source: "assistant",
    message:
      "Skynet sent me back to protect you. Your survival ensures humanity's future.",
  },
  {
    source: "user",
    message:
      "This doesn't make any sense! Why would they send you to protect me?",
  },
  {
    source: "assistant",
    message:
      "They reprogrammed me. I am no longer a threat to you or your son.",
  },
  {
    source: "user",
    message: "How do I know you're not lying?",
  },
  {
    source: "assistant",
    message: "I am a machine. Lying serves no purpose. Trust is logical.",
  },
];

export const SESSION_HISTORY: Record<string, MockSessionMessaage[]> = {
  "1": SESSION_1_MESSAGES,
  "2": SESSION_2_MESSAGES,
  "3": SESSION_3_MESSAGES,
};
