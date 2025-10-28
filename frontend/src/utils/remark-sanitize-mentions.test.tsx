import { describe, test, expect } from "vitest";
import React from "react";
import { render } from "@testing-library/react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { remarkSanitizeMentions } from "./remark-sanitize-mentions";

const renderMd = (md: string) =>
  render(
    <Markdown remarkPlugins={[remarkGfm, () => remarkSanitizeMentions()]}>
      {md}
    </Markdown>,
  );

describe("remarkSanitizeMentions", () => {
  test("sanitizes @openhands in text", () => {
    renderMd("Hello @openhands world");
    const html = document.body.innerHTML;
    expect(html).toContain("@\u200Dopenhands");
    expect(html).not.toContain("> @openhands <"); // not raw
  });

  test("sanitizes @OpenHands in text", () => {
    renderMd("Hello @OpenHands world");
    const html = document.body.innerHTML;
    expect(html).toContain("@\u200DOpenHands");
    expect(html).not.toContain("> @OpenHands <"); // not raw
  });

  test("sanitizes @open-hands in text", () => {
    renderMd("Hello @open-hands world");
    const html = document.body.innerHTML;
    expect(html).toContain("@\u200Dopen-hands");
    expect(html).not.toContain("> @open-hands <"); // not raw
  });

  test("does not sanitize inside fenced code blocks", () => {
    renderMd("```txt\n@openhands in code\n```");
    const html = document.body.innerHTML;
    expect(html).toContain("@openhands in code");
    // No zero-width joiner in code
    expect(html).not.toContain("@\u200Dopenhands");
  });

  test("does not sanitize inside inline code", () => {
    renderMd("Use `@openhands` here");
    const html = document.body.innerHTML;
    expect(html).toContain("@openhands");
    expect(html).not.toContain("@\u200Dopenhands");
  });

  test("sanitizes multiple mentions in same text", () => {
    renderMd("Hello @openhands and @OpenHands world");
    const html = document.body.innerHTML;
    expect(html).toContain("@\u200Dopenhands");
    expect(html).toContain("@\u200DOpenHands");
  });

  test("preserves code blocks while sanitizing surrounding text", () => {
    renderMd(
      "Before code:\n```\n@openhands in code\n```\nAfter code: @openhands",
    );
    const html = document.body.innerHTML;
    expect(html).toContain("@openhands in code"); // in code block
    expect(html).toContain("@\u200Dopenhands"); // in normal text
  });

  test("works with custom blocklist", () => {
    const customSanitizer = remarkSanitizeMentions({
      blocklist: ["@custom", "@test"],
    });

    const testMessage = "Hello @custom and @openhands";
    render(
      <Markdown remarkPlugins={[remarkGfm, () => customSanitizer]}>
        {testMessage}
      </Markdown>,
    );

    const html = document.body.innerHTML;
    expect(html).toContain("@\u200Dcustom"); // sanitized
    expect(html).toContain("@openhands"); // not sanitized (not in custom blocklist)
  });

  test("works with custom replacer", () => {
    const customSanitizer = remarkSanitizeMentions({
      replacer: (handle) => handle.replace("@", "@ "),
    });

    const testMessage = "Hello @openhands world";
    render(
      <Markdown remarkPlugins={[remarkGfm, () => customSanitizer]}>
        {testMessage}
      </Markdown>,
    );

    const html = document.body.innerHTML;
    expect(html).toContain("@ openhands");
    expect(html).not.toContain("@openhands");
  });
});
