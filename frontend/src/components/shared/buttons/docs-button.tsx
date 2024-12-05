import DocsIcon from "#/icons/docs.svg?react";

export function DocsButton() {
  return (
    <a
      href="https://docs.all-hands.dev"
      aria-label="Documentation"
      target="_blank"
      rel="noreferrer noopener"
      className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
    >
      <DocsIcon width={28} height={28} />
    </a>
  );
}
