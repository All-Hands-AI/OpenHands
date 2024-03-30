import React, { useEffect, useState } from "react";
import "./App.css";
import ChatInterface from "./components/ChatInterface";
import Errors from "./components/Errors";
import SettingModal from "./components/SettingModal";
import {
  AGENTS,
  changeAgent,
  changeDirectory as sendChangeDirectorySocketMessage,
  changeModel,
  fetchModels,
  INITIAL_MODELS,
} from "./services/settingsService";
import Workspace from "./components/Workspace";

const cachedModels = JSON.parse(
  localStorage.getItem("supportedModels") || "[]",
);
const cachedAgents = JSON.parse(
  localStorage.getItem("supportedAgents") || "[]",
);

function App(): JSX.Element {
  const [settingOpen, setSettingOpen] = useState(false);
  const [workspaceDirectory, setWorkspaceDirectory] = useState(
    localStorage.getItem("workspaceDirectory") || "./workspace",
  );
  const [model, setModel] = useState(
    localStorage.getItem("model") || "gpt-3.5-turbo-1106",
  );
  const [supportedModels, setSupportedModels] = useState(
    cachedModels.length > 0 ? cachedModels : INITIAL_MODELS,
  );
  const [agent, setAgent] = useState(
    localStorage.getItem("agent") || "LangchainsAgent",
  );
  const [supportedAgents] = useState(
    cachedAgents.length > 0 ? cachedAgents : AGENTS,
  );

  useEffect(() => {
    fetchModels().then((fetchedModels) => {
      setSupportedModels(fetchedModels);
      localStorage.setItem("supportedModels", JSON.stringify(fetchedModels));
    });
  }, []);

  const handleCloseModal = () => {
    setSettingOpen(false);
  };

  const handleSaveCfg = () => {
    sendChangeDirectorySocketMessage(workspaceDirectory);
    changeModel(model);
    changeAgent(agent);
    localStorage.setItem("model", model);
    localStorage.setItem("workspaceDirectory", workspaceDirectory);
    localStorage.setItem("agent", agent);
    setSettingOpen(false);
  };

  return (
    <div className="flex h-screen bg-bg-dark text-white">
      <Errors />
      <div className="flex-1 rounded-xl m-4 overflow-hidden bg-bg-light">
        <ChatInterface setSettingOpen={setSettingOpen} />
      </div>
      <div className="flex flex-col flex-1 m-4 overflow-hidden rounded-xl bg-bg-light">
        <Workspace />
      </div>

      <SettingModal
        isOpen={settingOpen}
        onClose={handleCloseModal}
        onSave={handleSaveCfg}
        workspaceDir={workspaceDirectory}
        setWorkspaceDir={setWorkspaceDirectory}
        model={model}
        setModel={setModel}
        supportedModels={supportedModels}
        agent={agent}
        setAgent={setAgent}
        supportedAgents={supportedAgents}
      />
    </div>
  );
}

export default App;
