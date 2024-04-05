function parseVersion(version) {
  return version.split('.').map(Number);
}

function compareVersions(v1, v2) {
  const v1Parts = parseVersion(v1);
  const v2Parts = parseVersion(v2);

  for (let i = 0; i < Math.max(v1Parts.length, v2Parts.length); i++) {
    const v1Part = v1Parts[i] || 0;
    const v2Part = v2Parts[i] || 0;

    if (v1Part > v2Part) return 1;
    if (v1Part < v2Part) return -1;
  }

  return 0;
}

const currentVersion = process.version.substring(1);
const targetVersion = "18.17.1";

if (compareVersions(currentVersion, targetVersion) >= 0) {
  console.log(`Current Node.js version is ${currentVersion}, corepack is supported.`);
} else {
  console.error(`Current Node.js version is ${currentVersion}, but corepack is unsupported. Required version: ^${targetVersion}.`);
  process.exit(1)
}
