import { visit } from "unist-util-visit";
import type { Root, Text } from "mdast";

type Options = {
  blocklist?: string[];
  replacer?: (handle: string) => string;
};

const DEFAULT_BLOCKLIST = ["@OpenHands", "@openhands", "@open-hands"];
const DEFAULT_REPLACER = (handle: string) => handle.replace("@", "@\u200D");

export function remarkSanitizeMentions(options?: Partial<Options>) {
  const blocklist = (
    options?.blocklist?.length ? options.blocklist : DEFAULT_BLOCKLIST
  )
    // normalize to a canonical set and include case variants
    .reduce<string[]>((acc, item) => {
      const variants = new Set([
        item,
        item.toLowerCase(),
        item.toUpperCase(),
        item[0] === "@" ? item : `@${item}`,
      ]);
      return acc.concat(Array.from(variants));
    }, []);

  const replacer = options?.replacer ?? DEFAULT_REPLACER;

  const pattern = new RegExp(
    `(${blocklist.map((s) => s.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&")).join("|")})`,
    "g",
  );

  return function transformer(tree: Root) {
    visit(tree, "text", (node: Text) => {
      const { value } = node;
      if (!value || !pattern.test(value)) return;

      // Check if this text node is inside a code block
      // We'll use a simple approach: if the value contains code-like patterns, skip
      if (value.includes("```") || value.includes("`")) {
        return;
      }

      // Sanitize the text by creating a new value
      const sanitizedValue = value.replace(pattern, (m) => replacer(m));

      // Only update if the value actually changed
      if (sanitizedValue !== value) {
        Object.assign(node, { value: sanitizedValue });
      }
    });
  };
}
