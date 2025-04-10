export function getDiffPath(diff: string) {
  const diffPathRegex = /^[-+]{3}\s(.+)$/m;
  const diffMatch = diff.match(diffPathRegex);
  if (diffMatch) {
    return diffMatch[1];
  }

  const errorPathRegex =
    /(?:Invalid `path` parameter:|File already exists at:)\s(\/[\w\/\._-]+)/g;
  const matches = [...diff.matchAll(errorPathRegex)];
  if (matches.length > 0) {
    return matches[0][1];
  }

  const firstLine = diff.split("\n")[0];
  return firstLine || "";
}

export function getCommand(str: string) {
  const match = str.match(/`([^`]+)`/);
  if (match) {
    return match[1];
  }
  const firstLine = str.split("\n")[0];
  return firstLine || "";
}

export function getCatFilePath(str: string) {
  const catMatch = str.match(/running `cat -n` on ([^\n:]+):/);
  if (catMatch) {
    return catMatch[1];
  }

  const firstLine = str.split("\n")[0];
  return firstLine || "";
}

export function getUrlBrowser(str: string) {
  const urlRegex = /\bhttps?:\/\/[^\s<>[\]()]+/;
  const match = str.match(urlRegex);
  if (match) {
    return match[0];
  }
  const firstLine = str.split("\n")[0];
  return firstLine || "";
}
