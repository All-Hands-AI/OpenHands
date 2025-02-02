declare module "use-sound" {
  type PlayFunction = () => void;
  type HookOptions = {
    volume?: number;
    soundEnabled?: boolean;
    interrupt?: boolean;
    [key: string]: unknown;
  };

  export default function useSound(
    src: string,
    options?: HookOptions,
  ): [PlayFunction, { sound: unknown; stop: () => void }];
}
