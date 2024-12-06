import type { Config } from "@react-router/dev/config";

/**
 * This script is used to unpack the client directory from the frontend build directory.
 * Remix SPA mode builds the client directory into the build directory. This function
 * moves the contents of the client directory to the build directory and then removes the
 * client directory.
 *
 * This script is used in the buildEnd function of the Vite config.
 */
const unpackClientDirectory = async () => {
  const fs = await import("fs");
  const path = await import("path");

  const buildDir = path.resolve(__dirname, "build");
  const clientDir = path.resolve(buildDir, "client");

  const files = await fs.promises.readdir(clientDir);
  await Promise.all(
    files.map((file) =>
      fs.promises.rename(
        path.resolve(clientDir, file),
        path.resolve(buildDir, file),
      ),
    ),
  );

  await fs.promises.rmdir(clientDir);
};

export default {
  appDirectory: "src",
  buildEnd: unpackClientDirectory,
  ssr: false,
} satisfies Config;
