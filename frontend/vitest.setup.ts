import { server } from "#/mocks/node";
import "@testing-library/jest-dom";

// @ts-expect-error - Mock for Terminal tests
HTMLCanvasElement.prototype.getContext = vi.fn();

// Mock the i18n provider
vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({ t: (key: string) => key }),
}));

// Mock requests during tests
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
