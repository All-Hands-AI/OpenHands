// learn more: https://github.com/testing-library/jest-dom
// eslint-disable-next-line import/no-extraneous-dependencies
import "@testing-library/jest-dom";

// @ts-expect-error - Mock for Terminal tests
HTMLCanvasElement.prototype.getContext = vi.fn();

// Mock the i18n provider
vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({ t: (key: string) => key }),
}));
