import type { Mock } from "vitest";
import { getToken } from "./auth";

Storage.prototype.getItem = vi.fn();
Storage.prototype.setItem = vi.fn();

describe("Auth Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getToken", () => {
    it("should fetch and return a token", async () => {
      (Storage.prototype.getItem as Mock).mockReturnValue("newToken");
      const data = await getToken();
      expect(localStorage.getItem).toHaveBeenCalledWith("token"); // Used to set Authorization header
      expect(data).toEqual("newToken");
    });
  });
});
