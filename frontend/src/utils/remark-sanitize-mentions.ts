import { visit, SKIP } from "unist-util-visit";
import type { Root, Content, Text } from "mdast";

type Options = {
  blocklist: string[];
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
    visit(
      tree,
      "text",
      (node: Text, index: number | null, parent: Content | Root | null) => {
        if (!parent) return;

        // Skip text nodes that are inside code-like nodes
        // We skip if any ancestor is code, inlineCode, or link/code container
        // react-markdown won't render mentions clickable inside code anyway, but we protect per acceptance criteria.
        let ancestor: Content | Root | null = parent;
        while (ancestor) {
          if (ancestor.type === "code" || ancestor.type === "inlineCode")
            return SKIP;
          ancestor = (ancestor as any).parent || null;
        }

        const { value } = node;
        if (!value || !pattern.test(value)) return;

        // Create a new node with sanitized value instead of mutating
        const sanitizedNode: Text = {
          ...node,
          value: value.replace(pattern, (m) => replacer(m))
        };

        // Replace the node in the parent
        if (index !== null && Array.isArray(parent.children)) {
          parent.children[index] = sanitizedNode;
        }
      },
    );
  };
}
