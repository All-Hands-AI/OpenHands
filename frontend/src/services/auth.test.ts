import * as jose from "jose";
import type { Mock } from "vitest";
import { getToken } from "./auth";

vi.mock("jose", () => ({
  decodeJwt: vi.fn(),
}));

Storage.prototype.getItem = vi.fn();
Storage.prototype.setItem = vi.fn();

describe("Auth Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getToken", () => {
    it("should fetch and return a token", async () => {
      const data = await getToken();
      (Storage.prototype.getItem as Mock).mockReturnValue("newToken");
      expect(localStorage.getItem).toHaveBeenCalledWith("token"); // Used to set Authorization header
      expect(data).toEqual({ token: "newToken" });
    });
  });

});
