import { expect, test } from "vitest";
import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";

test("extractNextPageFromLink", () => {
  const link = `<https://api.github.com/repositories/1300192/issues?page=2>; rel="prev", <https://api.github.com/repositories/1300192/issues?page=4>; rel="next", <https://api.github.com/repositories/1300192/issues?page=515>; rel="last", <https://api.github.com/repositories/1300192/issues?page=1>; rel="first"`;
  expect(extractNextPageFromLink(link)).toBe(4);

  const noNextLink = `<https://api.github.com/repositories/1300192/issues?page=2>; rel="prev", <https://api.github.com/repositories/1300192/issues?page=1>; rel="first"`;
  expect(extractNextPageFromLink(noNextLink)).toBeNull();
});
