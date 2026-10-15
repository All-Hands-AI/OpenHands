import type { ElementContent, Root, RootContent } from "hast";

/** Must match the `stream-word-fade` animation in index.css. */
export const STREAM_WORD_FADE_MS = 280;

/** Text inside these is not split into words. */
const SKIP_TAGS = new Set(["pre", "code", "svg", "math", "script", "style"]);

const now = () =>
  typeof performance !== "undefined" ? performance.now() : Date.now();

/**
 * Records when each part of a streamed text was revealed, so a word's fade can
 * be resumed where it was rather than restarted when its element is re-created
 * (a streamed block is re-mounted when the block before it is frozen).
 */
export class RevealClock {
  private segments: { start: number; at: number }[] = [];

  private settledBefore = 0;

  private length = 0;

  /** The text now shown is `length` long. */
  advance(length: number, at = now()) {
    if (length > this.length) {
      this.segments.push({ start: this.length, at });
      this.length = length;
    }
    // Segments whose fade is over no longer need a time.
    while (
      this.segments.length > 0 &&
      at - this.segments[0].at >= STREAM_WORD_FADE_MS
    ) {
      this.segments.shift();
      this.settledBefore = this.segments[0]?.start ?? this.length;
    }
  }

  /** Treat text up to `length` as already shown, e.g. after a retry snapped in. */
  reset(length: number) {
    this.segments = [];
    this.settledBefore = length;
    this.length = length;
  }

  /** When the character at `offset` was revealed, or null if long enough ago. */
  revealedAt(offset: number): number | null {
    if (offset < this.settledBefore) {
      return null;
    }
    for (let i = this.segments.length - 1; i >= 0; i -= 1) {
      if (this.segments[i].start <= offset) {
        return this.segments[i].at;
      }
    }
    return null;
  }
}

interface FadeInWordsOptions {
  clock: RevealClock;
  /** Offset of this block's source within the whole streamed text. */
  blockStart: number;
}

/**
 * Wrap each word of a streamed reply in a span, and fade in the ones revealed
 * within the last `STREAM_WORD_FADE_MS`. Every word keeps a span (not only the
 * fading ones) so elements stay put as text is appended; a negative
 * `animation-delay` places a re-created word at its current point in the fade.
 *
 * Text nodes after inline markup carry no source position, so their offsets
 * continue from the previous one — off by the markup's few characters, which
 * is invisible in the timing.
 */
export function rehypeFadeInWords({ clock, blockStart }: FadeInWordsOptions) {
  return (tree: Root) => {
    const renderedAt = now();
    let cursor = 0;

    const splitWords = (value: string, start: number): ElementContent[] => {
      const parts: ElementContent[] = [];
      let index = 0;
      for (const part of value.split(/(\s+)/)) {
        if (part && /\S/.test(part)) {
          const revealedAt = clock.revealedAt(blockStart + start + index);
          const elapsed =
            revealedAt === null ? Infinity : renderedAt - revealedAt;
          parts.push({
            type: "element",
            tagName: "span",
            properties:
              elapsed < STREAM_WORD_FADE_MS
                ? {
                    dataStreamWord: true,
                    className: ["stream-word-fade"],
                    style: `animation-delay:${-Math.round(elapsed)}ms`,
                  }
                : { dataStreamWord: true },
            children: [{ type: "text", value: part }],
          });
        } else if (part) {
          parts.push({ type: "text", value: part });
        }
        index += part.length;
      }
      return parts;
    };

    const wrap = <T extends RootContent | ElementContent>(children: T[]): T[] =>
      children.flatMap((child) => {
        if (child.type === "text") {
          const offset = child.position?.start.offset;
          if (offset !== undefined) {
            cursor = offset;
          }
          const start = cursor;
          cursor += child.value.length;
          return splitWords(child.value, start) as T[];
        }
        if (child.type === "element" && !SKIP_TAGS.has(child.tagName)) {
          // eslint-disable-next-line no-param-reassign
          child.children = wrap(child.children);
        }
        return [child];
      });

    // eslint-disable-next-line no-param-reassign
    tree.children = wrap(tree.children);
  };
}
