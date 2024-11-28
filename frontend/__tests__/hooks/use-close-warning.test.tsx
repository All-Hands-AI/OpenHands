import { renderHook } from "@testing-library/react";
import { useCloseWarning } from "#/hooks/use-close-warning";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { rootReducer } from "#/store";
import { UserPrefsProvider } from "#/context/user-prefs-context";
import AgentState from "#/types/agent-state";
import { test, expect, vi, beforeEach, afterEach } from "vitest";

const mockSettings = {
  CLOSE_WARNING: "while_working",
  LLM_MODEL: "",
  LLM_BASE_URL: "",
  AGENT: "",
  LANGUAGE: "en",
  LLM_API_KEY: "",
  CONFIRMATION_MODE: false,
  SECURITY_ANALYZER: "",
};

const createStore = (agentState = AgentState.FINISHED) => configureStore({
  reducer: rootReducer,
  preloadedState: {
    agent: {
      curAgentState: agentState,
    },
    fileState: {
      files: [],
      selectedPath: null,
      modifiedFiles: {},
    },
    initalQuery: {
      selectedRepository: null,
    },
    browser: {
      url: "",
      isLoading: false,
      error: null,
    },
    chat: {
      messages: [],
      isLoading: false,
      error: null,
    },
    code: {
      content: "",
      isLoading: false,
      error: null,
    },
    cmd: {
      output: "",
      isLoading: false,
      error: null,
    },
    jupyter: {
      cells: [],
      isLoading: false,
      error: null,
    },
    securityAnalyzer: {
      isLoading: false,
      error: null,
    },
    status: {
      isLoading: false,
      error: null,
    },
  },
});

const mockStore = createStore();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <Provider store={mockStore}>
    <UserPrefsProvider initialSettings={mockSettings}>
      {children}
    </UserPrefsProvider>
  </Provider>
);

beforeEach(() => {
  window.addEventListener = vi.fn();
  window.removeEventListener = vi.fn();
});

afterEach(() => {
  vi.clearAllMocks();
});

test("should add and remove event listener", () => {
  const { unmount } = renderHook(() => useCloseWarning(), { wrapper });

  expect(window.addEventListener).toHaveBeenCalledWith(
    "beforeunload",
    expect.any(Function)
  );

  unmount();

  expect(window.removeEventListener).toHaveBeenCalledWith(
    "beforeunload",
    expect.any(Function)
  );
});

test("should prevent unload when agent is working and setting is while_working", () => {
  const store = createStore(AgentState.RUNNING);

  const customWrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>
      <UserPrefsProvider initialSettings={mockSettings}>
        {children}
      </UserPrefsProvider>
    </Provider>
  );

  renderHook(() => useCloseWarning(), { wrapper: customWrapper });

  const addEventListenerMock = window.addEventListener as unknown as vi.Mock;
  const handler = addEventListenerMock.mock.calls[0][1];

  const mockEvent = {
    preventDefault: vi.fn(),
    returnValue: "",
  };

  handler(mockEvent);

  expect(mockEvent.preventDefault).toHaveBeenCalled();
});

test("should not prevent unload when agent is not working and setting is while_working", () => {
  renderHook(() => useCloseWarning(), { wrapper });

  const addEventListenerMock = window.addEventListener as unknown as vi.Mock;
  const handler = addEventListenerMock.mock.calls[0][1];

  const mockEvent = {
    preventDefault: vi.fn(),
    returnValue: "",
  };

  handler(mockEvent);

  expect(mockEvent.preventDefault).not.toHaveBeenCalled();
});

test("should always prevent unload when setting is always", () => {
  const customSettings = {
    ...mockSettings,
    CLOSE_WARNING: "always",
  };

  const customWrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={mockStore}>
      <UserPrefsProvider initialSettings={customSettings}>
        {children}
      </UserPrefsProvider>
    </Provider>
  );

  renderHook(() => useCloseWarning(), { wrapper: customWrapper });

  const addEventListenerMock = window.addEventListener as unknown as vi.Mock;
  const handler = addEventListenerMock.mock.calls[0][1];

  const mockEvent = {
    preventDefault: vi.fn(),
    returnValue: "",
  };

  handler(mockEvent);

  expect(mockEvent.preventDefault).toHaveBeenCalled();
});

test("should never prevent unload when setting is never", () => {
  const customSettings = {
    ...mockSettings,
    CLOSE_WARNING: "never",
  };

  const customWrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={mockStore}>
      <UserPrefsProvider initialSettings={customSettings}>
        {children}
      </UserPrefsProvider>
    </Provider>
  );

  renderHook(() => useCloseWarning(), { wrapper: customWrapper });

  const addEventListenerMock = window.addEventListener as unknown as vi.Mock;
  const handler = addEventListenerMock.mock.calls[0][1];

  const mockEvent = {
    preventDefault: vi.fn(),
    returnValue: "",
  };

  handler(mockEvent);

  expect(mockEvent.preventDefault).not.toHaveBeenCalled();
});
