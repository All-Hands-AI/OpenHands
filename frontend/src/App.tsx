import { useDisclosure } from "@nextui-org/react";
import React, { useEffect, useState, useMemo } from "react";
import { useSelector } from "react-redux";
import { Toaster } from "react-hot-toast";
import i18next from "i18next";
import { ThemeSwitcherProvider } from "react-css-theme-switcher";
import { useThemeSwitch } from "#/hooks/useThemeSwitch";
import {
  getThemeMap,
  getDefaultTheme,
  isValidTheme,
  Theme,
} from "#/utils/themeUtils";
import ChatInterface from "#/components/chat/ChatInterface";
import Errors from "#/components/Errors";
import { Container, Orientation } from "#/components/Resizable";
import Workspace from "#/components/Workspace";
import LoadPreviousSessionModal from "#/components/modals/load-previous-session/LoadPreviousSessionModal";
import SettingsPage from "#/components/modals/settings/SettingsPage";
import AgentControlBar from "./components/AgentControlBar";
import AgentStatusBar from "./components/AgentStatusBar";
import Terminal from "./components/terminal/Terminal";
import Session from "#/services/session";
import { getToken } from "#/services/auth";
import {
  getSettings,
  saveSettings,
  settingsAreUpToDate,
  Settings,
} from "#/services/settings";
import { RootState } from "./store";
import AgentState from "./types/AgentState";
import { fetchAgents, fetchModels } from "#/services/options";
import toast from "#/utils/toast";
import "./App.css";
import LeftPushout from "./components/LeftPushout";
import { AvailableLanguages } from "#/i18n";

function Controls(): JSX.Element {
  return (
    <div className="flex w-full p-4 bg-bg-dark items-center shrink-0 justify-between">
      <div className="flex items-center gap-4">
        <AgentControlBar />
      </div>
      <AgentStatusBar />
    </div>
  );
}

// React.StrictMode will cause double rendering, use this to prevent it
let initOnce = false;

function AppContent(): JSX.Element {
  const { onOpen: onSettingsPageOpen } = useDisclosure();
  const {
    isOpen: loadPreviousSessionModalIsOpen,
    onOpen: onLoadPreviousSessionModalOpen,
    onOpenChange: onLoadPreviousSessionModalOpenChange,
  } = useDisclosure();

  const [settingsPageIsOpen, setSettingsPageIsOpen] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [agents, setAgents] = useState<string[]>([]);
  const [settings, setSettings] = useState<Settings>(getSettings());

  const curAgentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );

  const [criticalError, setCriticalError] = useState<Error | null>(null);
  const handleError = (err: Error, isCritical: boolean = false) => {
    if (isCritical) {
      setCriticalError(err);
    }
    toast.error(err.name, err.message);
  };

  const handleSettingsClose = () => setSettingsPageIsOpen(false);
  const handleSettingsOpen = () => setSettingsPageIsOpen(true);

  const handleModelChange = (model: string) => {
    setSettings((prev) => ({
      ...prev,
      LLM_MODEL: model,
    }));
  };

  const handleAgentChange = (agent: string) => {
    setSettings((prev) => ({ ...prev, AGENT: agent }));
  };

  const handleLanguageChange = (language: string) => {
    const key =
      AvailableLanguages.find((lang) => lang.label === language)?.value ||
      language;
    setSettings((prev) => ({ ...prev, LANGUAGE: key }));
  };

  const handleAPIKeyChange = (key: string) => {
    setSettings((prev) => ({ ...prev, LLM_API_KEY: key }));
  };

  const { theme, setTheme } = useThemeSwitch(getDefaultTheme());

  const handleThemeChange = (newTheme: Theme) => {
    if (isValidTheme(newTheme)) {
      setTheme(newTheme);
      setSettings((prev) => ({ ...prev, THEME: newTheme }));
      saveSettings({ ...settings, THEME: newTheme });
      toast.settingsChanged(`Theme set to "${newTheme}"`);
    }
  };

  const handleSaveSettings = (newSettings: Settings) => {
    const currentSettings = getSettings();
    const updatedSettings: Partial<Settings> = {};

    // Determine which settings have actually changed
    Object.keys(newSettings).forEach((key) => {
      if (
        newSettings[key as keyof Settings] !==
        currentSettings[key as keyof Settings]
      ) {
        updatedSettings[key as keyof Settings] =
          newSettings[key as keyof Settings];
      }
    });

    // Check if only the theme has changed
    const onlyThemeChanged =
      Object.keys(updatedSettings).length === 1 && "THEME" in updatedSettings;

    saveSettings(newSettings);
    setSettings(newSettings);

    // Only change language if it has been updated
    if ("LANGUAGE" in updatedSettings) {
      i18next.changeLanguage(newSettings.LANGUAGE);
    }

    // Start a new session only if changes other than theme were made
    if (!onlyThemeChanged) {
      Session.startNewSession();
    }

    const sensitiveKeys = ["LLM_API_KEY"];

    Object.entries(updatedSettings).forEach(([key, value]) => {
      // TODO translations!
      if (!sensitiveKeys.includes(key)) {
        if (key !== "THEME") {
          toast.settingsChanged(`${key} set to "${value}"`);
        }
      } else {
        toast.settingsChanged(`${key} has been updated securely.`);
      }
    });

    // Only update API key in localStorage if it has changed
    if ("LLM_API_KEY" in updatedSettings) {
      localStorage.setItem(
        `API_KEY_${newSettings.LLM_MODEL || models[0]}`,
        newSettings.LLM_API_KEY,
      );
    }
  };

  // Memoize the LeftPushout component
  const memoizedLeftPushout = useMemo(
    () => (
      <LeftPushout onSettingsOpen={handleSettingsOpen}>
        <div className="flex items-center justify-center p-4">
          <img
            src="/src/assets/logo.png"
            alt="OpenDevin Logo"
            className="w-5 h-auto"
          />
          <div className="ml-4 text-base font-bold">OpenDevin</div>
        </div>
      </LeftPushout>
    ),
    [handleSettingsOpen],
  );

  useEffect(() => {
    const storedSettings = getSettings();
    setSettings(storedSettings);
    if (isValidTheme(storedSettings.THEME)) setTheme(storedSettings.THEME);
  }, []);

  useEffect(() => {
    // only for startup!
    if (initOnce) return;
    initOnce = true;

    // Fetch models and agents first
    const fetchData = async () => {
      try {
        const fetchedModels = await fetchModels();
        const fetchedAgents = await fetchAgents();
        setModels(fetchedModels);
        setAgents(fetchedAgents);
      } catch (err) {
        handleError(new Error("Error fetching models or agents"));
      }
    };

    // Initialize app state
    const initializeApp = () => {
      if (!settingsAreUpToDate()) {
        onSettingsPageOpen();
      } else if (getToken()) {
        onLoadPreviousSessionModalOpen();
      } else {
        Session.startNewSession();
      }
    };

    // Execute fetch and initialization
    fetchData()
      .then(initializeApp)
      .catch((err) => {
        handleError(new Error("Failed to initialize application"), err);
      });

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="h-screen w-screen flex">
      {memoizedLeftPushout}
      <div className="flex-grow flex flex-col">
        <div className="flex-grow flex bg-bg-dark text-foreground min-h-0 relative">
          {settingsPageIsOpen ? (
            <SettingsPage
              isOpen={settingsPageIsOpen}
              onClose={handleSettingsClose}
              models={models}
              agents={agents}
              settings={settings}
              agentIsRunning={curAgentState === AgentState.RUNNING}
              disabled={curAgentState === AgentState.RUNNING}
              theme={theme}
              onModelChange={handleModelChange}
              onAgentChange={handleAgentChange}
              onLanguageChange={handleLanguageChange}
              onAPIKeyChange={handleAPIKeyChange}
              onThemeChange={handleThemeChange}
              onSaveSettings={handleSaveSettings}
              onError={handleError}
            />
          ) : (
            <Container
              orientation={Orientation.HORIZONTAL}
              className="grow h-full min-h-0 min-w-0 px-3 pt-3"
              initialSize={500}
              firstChild={<ChatInterface />}
              firstClassName="min-w-[500px] rounded-xl overflow-hidden border border-border"
              secondChild={
                <Container
                  orientation={Orientation.VERTICAL}
                  className="grow h-full min-h-0 min-w-0"
                  initialSize={window.innerHeight - 300}
                  firstChild={<Workspace />}
                  firstClassName="min-h-72 rounded-xl border border-border bg-bg-workspace flex flex-col overflow-hidden"
                  secondChild={<Terminal />}
                  secondClassName="min-h-72 rounded-xl border border-border bg-bg-workspace"
                />
              }
              secondClassName="flex flex-col overflow-hidden grow min-w-[500px]"
            />
          )}
        </div>
        <Controls />
      </div>
      <LoadPreviousSessionModal
        isOpen={loadPreviousSessionModalIsOpen}
        onOpenChange={onLoadPreviousSessionModalOpenChange}
      />
      {criticalError && <Errors error={criticalError} />}
      <Toaster />
    </div>
  );
}

function App(): JSX.Element {
  const themes = getThemeMap("/themes/");
  const defaultTheme = getDefaultTheme();

  return (
    <ThemeSwitcherProvider themeMap={themes} defaultTheme={defaultTheme}>
      <AppContent />
    </ThemeSwitcherProvider>
  );
}

export default App;
