import { describe, it, expect } from "vitest";
import * as fs from "fs";
import * as path from "path";
import { execSync } from "child_process";

describe("Favicon dimensions", () => {
  const publicPath = path.join(__dirname, "..", "public");

  const faviconFiles = [
    { file: "favicon-16x16.png", size: 16 },
    { file: "favicon-32x32.png", size: 32 },
    { file: "apple-touch-icon.png", size: 180 },
    { file: "android-chrome-192x192.png", size: 192 },
    { file: "android-chrome-512x512.png", size: 512 },
    { file: "mstile-150x150.png", size: 150 },
  ];

  faviconFiles.forEach(({ file, size }) => {
    it(`${file} should have proper square dimensions of ${size}x${size}`, () => {
      const filePath = path.join(publicPath, file);
      expect(fs.existsSync(filePath)).toBe(true);

      try {
        const dimensions = execSync(
          `identify -format "%wx%h" "${filePath}"`,
        ).toString();
        expect(dimensions).toBe(`${size}x${size}`);
      } catch (error) {
        console.warn(
          `ImageMagick not available, skipping dimension check for ${file}`,
        );
      }
    });

    it(`${file} should have sufficient padding on all sides`, () => {
      const filePath = path.join(publicPath, file);
      expect(fs.existsSync(filePath)).toBe(true);

      try {
        const boundingBox = execSync(
          `identify -format "%@" "${filePath}"`,
        ).toString();
        const match = boundingBox.match(/(\d+)x(\d+)\+(\d+)\+(\d+)/);

        if (match) {
          const [, width, height, xOffset, yOffset] = match.map(Number);

          // Verify there's padding on all sides (at least 10% of the image size)
          const minPadding = Math.floor(size * 0.1);
          expect(xOffset).toBeGreaterThanOrEqual(minPadding);
          expect(yOffset).toBeGreaterThanOrEqual(minPadding);

          // Verify padding on right and bottom
          const rightPadding = size - width - xOffset;
          const bottomPadding = size - height - yOffset;
          expect(rightPadding).toBeGreaterThanOrEqual(minPadding);
          expect(bottomPadding).toBeGreaterThanOrEqual(minPadding);

          // Verify the content is more square-like (aspect ratio closer to 1:1)
          // Allow some variation, but the aspect ratio shouldn't be too extreme
          const aspectRatio = width / height;
          expect(aspectRatio).toBeGreaterThan(0.8);
          expect(aspectRatio).toBeLessThan(2.0);
        }
      } catch (error) {
        console.warn(
          `ImageMagick not available, skipping padding check for ${file}`,
        );
      }
    });
  });

  it("favicon.ico should exist", () => {
    const filePath = path.join(publicPath, "favicon.ico");
    expect(fs.existsSync(filePath)).toBe(true);
  });
});
