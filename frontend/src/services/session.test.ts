import type { Mock } from "vitest";
import {
  ResDelMsg,
  ResFetchMsg,
  ResFetchMsgTotal,
  ResFetchMsgs,
} from "../types/ResponseType";
import { clearMsgs, fetchMsgTotal, fetchMsgs } from "./session";

// SUGGESTION: Prefer using msw for mocking requests (see https://mswjs.io/)
global.fetch = vi.fn();
Storage.prototype.getItem = vi.fn();

describe("Session Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Used to set Authorization header
    expect(localStorage.getItem).toHaveBeenCalledWith("token");
  });

  describe("fetchMsgTotal", () => {
    it("should fetch and return message total", async () => {
      const expectedResult: ResFetchMsgTotal = {
        msg_total: 10,
      };

      (fetch as Mock).mockImplementationOnce(() =>
        Promise.resolve({
          status: 200,
          json: () => Promise.resolve(expectedResult),
        }),
      );

      const data = await fetchMsgTotal();

      expect(fetch).toHaveBeenCalledWith(`/api/messages/total`, {
        headers: expect.any(Headers),
      });

      expect(data).toEqual(expectedResult);
    });

    it("throws an error if response status is not 200", async () => {
      // NOTE: The current implementation ONLY handles 200 status;
      // this means throwing even with a status of 201, 204, etc.
      (fetch as Mock).mockImplementationOnce(() =>
        Promise.resolve({ status: 401 }),
      );

      await expect(fetchMsgTotal()).rejects.toThrow(
        "Get message total failed.",
      );
    });
  });

  describe("fetchMsgs", () => {
    it("should fetch and return messages", async () => {
      const expectedResult: ResFetchMsgs = {
        messages: [
          {
            id: "1",
            role: "user",
            payload: {} as ResFetchMsg["payload"],
          },
        ],
      };

      (fetch as Mock).mockImplementationOnce(() =>
        Promise.resolve({
          status: 200,
          json: () => Promise.resolve(expectedResult),
        }),
      );

      const data = await fetchMsgs();

      expect(fetch).toHaveBeenCalledWith(`/api/messages`, {
        headers: expect.any(Headers),
      });

      expect(data).toEqual(expectedResult);
    });

    it("throws an error if response status is not 200", async () => {
      (fetch as Mock).mockImplementationOnce(() =>
        Promise.resolve({ status: 401 }),
      );

      await expect(fetchMsgs()).rejects.toThrow("Get messages failed.");
    });
  });

  describe("clearMsgs", () => {
    it("should clear messages", async () => {
      const expectedResult: ResDelMsg = {
        ok: "true",
      };

      (fetch as Mock).mockImplementationOnce(() =>
        Promise.resolve({
          status: 200,
          json: () => Promise.resolve(expectedResult),
        }),
      );

      const data = await clearMsgs();

      expect(fetch).toHaveBeenCalledWith(`/api/messages`, {
        method: "DELETE",
        headers: expect.any(Headers),
      });

      expect(data).toEqual(expectedResult);
    });

    it("throws an error if response status is not 200", async () => {
      (fetch as Mock).mockImplementationOnce(() =>
        Promise.resolve({ status: 401 }),
      );

      await expect(clearMsgs()).rejects.toThrow("Delete messages failed.");
    });
  });
});
