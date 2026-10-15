// @vitest-environment node
import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import { createServer, type AddressInfo, type Server } from "node:net";
import { homedir, tmpdir } from "node:os";
import path from "node:path";
import {
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  existsSync,
  rmSync,
} from "node:fs";
import {
  allocateMockLlmPorts,
  MOCK_LLM_PORT_SNAPSHOT_ENV,
} from "../../tests/e2e/mock-llm/utils/allocate-mock-llm-ports";
import globalTeardown from "../../tests/e2e/mock-llm/utils/global-teardown";
import { uvCacheEnvForIsolatedHome } from "../../tests/e2e/mock-llm/utils/uv-cache-env";

function listen(port: number): Promise<Server> {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(port, "127.0.0.1", () => resolve(server));
  });
}

function closeServer(server: Server): Promise<void> {
  return new Promise((resolve) => {
    server.close(() => resolve());
  });
}

describe("mock-LLM runner isolation", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe("user skills directory isolation", () => {
    it("never resolves to the real user's homedir/.openhands/skills", async () => {
      delete process.env.MOCK_LLM_USER_SKILLS_HOST_DIR;
      delete process.env.MOCK_LLM_TEST_HOME;
      delete process.env.OH_CANVAS_SAFE_STATE_DIR;

      const helpers =
        await import("../../tests/e2e/mock-llm/utils/skill-test-helpers");
      const realUserSkills = path.join(homedir(), ".openhands", "skills");

      expect(helpers.USER_SKILLS_DIR).not.toBe(realUserSkills);
      expect(helpers.USER_SKILLS_DIR).toContain(".tmp");
    });

    it("prefers MOCK_LLM_USER_SKILLS_HOST_DIR when set", async () => {
      const customPath = "/custom/user/skills";
      process.env.MOCK_LLM_USER_SKILLS_HOST_DIR = customPath;

      const helpers =
        await import("../../tests/e2e/mock-llm/utils/skill-test-helpers");
      expect(helpers.USER_SKILLS_DIR).toBe(path.resolve(customPath));
    });

    it("uses MOCK_LLM_TEST_HOME/.openhands/skills when test home is set", async () => {
      delete process.env.MOCK_LLM_USER_SKILLS_HOST_DIR;
      const testHome = "/tmp/test-home-dir";
      process.env.MOCK_LLM_TEST_HOME = testHome;

      const helpers =
        await import("../../tests/e2e/mock-llm/utils/skill-test-helpers");
      expect(helpers.USER_SKILLS_DIR).toBe(
        path.join(path.resolve(testHome), ".openhands", "skills"),
      );
    });

    it("derives from OH_CANVAS_SAFE_STATE_DIR parent when neither override is set", async () => {
      delete process.env.MOCK_LLM_USER_SKILLS_HOST_DIR;
      delete process.env.MOCK_LLM_TEST_HOME;
      const stateDir = "/tmp/mock-llm-123/state";
      process.env.OH_CANVAS_SAFE_STATE_DIR = stateDir;

      const helpers =
        await import("../../tests/e2e/mock-llm/utils/skill-test-helpers");
      expect(helpers.USER_SKILLS_DIR).toBe(
        path.join(
          path.dirname(path.resolve(stateDir)),
          "home",
          ".openhands",
          "skills",
        ),
      );
    });
  });

  describe("port allocation across config evaluations", () => {
    const servers: Server[] = [];

    afterEach(async () => {
      await Promise.all(servers.splice(0).map((server) => closeServer(server)));
    });

    it("reuses the first ports when a later evaluation finds them busy", async () => {
      const env: NodeJS.ProcessEnv = {};
      const specs = [
        {
          name: "ingress" as const,
          envName: "MOCK_LLM_INGRESS_PORT",
          preferred: 0,
        },
        { name: "mockLlm" as const, envName: "MOCK_LLM_PORT", preferred: 0 },
      ];

      const first = await allocateMockLlmPorts(specs, "npm", env);
      servers.push(
        await listen(Number(first.ingress)),
        await listen(Number(first.mockLlm)),
      );

      const second = await allocateMockLlmPorts(
        specs.map((spec) => ({
          ...spec,
          preferred: Number(first[spec.name]),
        })),
        "npm",
        env,
      );

      expect(second).toEqual(first);
      expect(env.MOCK_LLM_INGRESS_PORT).toBe(first.ingress);
      expect(env.MOCK_LLM_PORT).toBe(first.mockLlm);
    });

    it("keeps an explicit preferred port on the first allocation", async () => {
      const held = await listen(0);
      const preferred = (held.address() as AddressInfo).port;
      await closeServer(held);

      const env: NodeJS.ProcessEnv = {};
      const allocated = await allocateMockLlmPorts(
        [
          {
            name: "ingress",
            envName: "MOCK_LLM_INGRESS_PORT",
            preferred,
          },
        ],
        "npm",
        env,
      );

      expect(allocated.ingress).toBe(String(preferred));
      expect(JSON.parse(env[MOCK_LLM_PORT_SNAPSHOT_ENV] ?? "")).toEqual({
        scope: "npm",
        ports: { ingress: preferred },
      });
    });

    it("does not reallocate when the snapshot is missing a requested port", async () => {
      const env: NodeJS.ProcessEnv = {
        [MOCK_LLM_PORT_SNAPSHOT_ENV]: JSON.stringify({
          scope: "npm",
          ports: { ingress: 18300 },
        }),
        MOCK_LLM_PORT: "9999",
      };

      await expect(
        allocateMockLlmPorts(
          [
            {
              name: "ingress",
              envName: "MOCK_LLM_INGRESS_PORT",
              preferred: 1,
            },
            { name: "mockLlm", envName: "MOCK_LLM_PORT", preferred: 1 },
          ],
          "npm",
          env,
        ),
      ).rejects.toThrow(/mockLlm/);
      expect(env.MOCK_LLM_PORT).toBe("9999");
    });

    it("allocates again when the snapshot belongs to the other config", async () => {
      const env: NodeJS.ProcessEnv = {
        [MOCK_LLM_PORT_SNAPSHOT_ENV]: JSON.stringify({
          scope: "npm",
          ports: { ingress: 1 },
        }),
      };

      const allocated = await allocateMockLlmPorts(
        [
          {
            name: "ingress",
            envName: "MOCK_LLM_INGRESS_PORT",
            preferred: 0,
          },
        ],
        "docker",
        env,
      );

      expect(allocated.ingress).not.toBe("1");
      expect(JSON.parse(env[MOCK_LLM_PORT_SNAPSHOT_ENV] ?? "").scope).toBe(
        "docker",
      );
    });
  });

  describe("uv cache while HOME is isolated", () => {
    it("keeps uv cache and Python installs on the runner home", () => {
      expect(uvCacheEnvForIsolatedHome("/home/runner")).toEqual({
        UV_CACHE_DIR: path.join("/home/runner", ".cache", "uv"),
        UV_PYTHON_INSTALL_DIR: path.join(
          "/home/runner",
          ".local",
          "share",
          "uv",
          "python",
        ),
      });
    });

    it("honors explicit UV_CACHE_DIR and UV_PYTHON_INSTALL_DIR", () => {
      expect(
        uvCacheEnvForIsolatedHome("/home/runner", {
          UV_CACHE_DIR: "/opt/uv-cache",
          UV_PYTHON_INSTALL_DIR: "  /opt/uv-python  ",
        }),
      ).toEqual({
        UV_CACHE_DIR: "/opt/uv-cache",
        UV_PYTHON_INSTALL_DIR: "/opt/uv-python",
      });
    });
  });

  describe("globalTeardown", () => {
    let tempDir: string;

    beforeEach(() => {
      tempDir = mkdtempSync(path.join(tmpdir(), "teardown-test-"));
    });

    afterEach(() => {
      if (existsSync(tempDir)) {
        rmSync(tempDir, { recursive: true, force: true });
      }
    });

    it("removes MOCK_LLM_RUN_DIR during normal teardown", async () => {
      const dummyRunDir = path.join(tempDir, "mock-run");
      mkdirSync(dummyRunDir, { recursive: true });
      writeFileSync(path.join(dummyRunDir, "state.txt"), "data");
      expect(existsSync(dummyRunDir)).toBe(true);

      process.env.MOCK_LLM_RUN_DIR = dummyRunDir;
      delete process.env.MOCK_LLM_PRESERVE_STATE;

      await globalTeardown();
      expect(existsSync(dummyRunDir)).toBe(false);
    });

    it("preserves MOCK_LLM_RUN_DIR when MOCK_LLM_PRESERVE_STATE is truthy", async () => {
      const dummyRunDir = path.join(tempDir, "mock-run-preserved");
      mkdirSync(dummyRunDir, { recursive: true });
      writeFileSync(path.join(dummyRunDir, "state.txt"), "data");

      process.env.MOCK_LLM_RUN_DIR = dummyRunDir;
      process.env.MOCK_LLM_PRESERVE_STATE = "1";

      await globalTeardown();
      expect(existsSync(dummyRunDir)).toBe(true);
    });

    it("refuses to delete root, homedir, or cwd", async () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      process.env.MOCK_LLM_RUN_DIR = homedir();
      delete process.env.MOCK_LLM_PRESERVE_STATE;

      await globalTeardown();
      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining(
          "Refusing to delete unsafe per-run state directory",
        ),
      );
      warnSpy.mockRestore();
    });
  });
});
