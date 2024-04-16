import * as jose from "jose";
import { fetchToken, validateToken, getToken } from "./auth";

jest.mock("jose", () => ({
  decodeJwt: jest.fn(),
}));

// SUGGESTION: Prefer using msw for mocking requests (see https://mswjs.io/)
global.fetch = jest.fn(() =>
  Promise.resolve({
    status: 200,
    json: () => Promise.resolve({ token: "newToken" }),
  }),
) as jest.Mock;

describe("Auth Service", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Storage.prototype.getItem = jest.fn();
    Storage.prototype.setItem = jest.fn();
  });

  describe("fetchToken", () => {
    it("should fetch and return a token", async () => {
      const data = await fetchToken();

      expect(localStorage.getItem).toHaveBeenCalledWith("token"); // Used to set Authorization header
      expect(data).toEqual({ token: "newToken" });
      expect(fetch).toHaveBeenCalledWith(`/api/auth`, {
        headers: expect.any(Headers),
      });
    });

    it("throws an error if response status is not 200", async () => {
      (fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({ status: 401 }),
      );
      await expect(fetchToken()).rejects.toThrow("Get token failed.");
    });
  });

  describe("validateToken", () => {
    it("returns true for a valid token", () => {
      (jose.decodeJwt as jest.Mock).mockReturnValue({ sid: "123" });
      expect(validateToken("validToken")).toBe(true);
    });

    it("returns false for an invalid token", () => {
      (jose.decodeJwt as jest.Mock).mockReturnValue({});
      expect(validateToken("invalidToken")).toBe(false);
    });

    it("returns false when decodeJwt throws", () => {
      (jose.decodeJwt as jest.Mock).mockImplementation(() => {
        throw new Error("Invalid token");
      });
      expect(validateToken("badToken")).toBe(false);
    });
  });

  describe("getToken", () => {
    it("returns existing valid token from localStorage", async () => {
      (jose.decodeJwt as jest.Mock).mockReturnValue({ sid: "123" });
      (Storage.prototype.getItem as jest.Mock).mockReturnValue("existingToken");

      const token = await getToken();
      expect(token).toBe("existingToken");
    });

    it("fetches, validates, and stores a new token when existing token is invalid", async () => {
      (jose.decodeJwt as jest.Mock)
        .mockReturnValueOnce({})
        .mockReturnValueOnce({ sid: "123" });

      const token = await getToken();
      expect(token).toBe("newToken");
      expect(localStorage.setItem).toHaveBeenCalledWith("token", "newToken");
    });

    it("throws an error when fetched token is invalid", async () => {
      (jose.decodeJwt as jest.Mock).mockReturnValue({});
      await expect(getToken()).rejects.toThrow("Token validation failed.");
    });
  });
});
