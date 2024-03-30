import React, { ChangeEvent, useEffect, useState } from "react";
import {
  INITIAL_AGENTS,
  INITIAL_MODELS,
  changeAgent,
  changeModel,
  fetchAgents,
  fetchModels,
} from "../services/settingsService";
import "./css/BannerSettings.css";

function ModelSelect(): JSX.Element {
  const [models, setModels] = useState<string[]>(INITIAL_MODELS);
  useEffect(() => {
    fetchModels().then((fetchedModels) => {
      setModels(fetchedModels);
    });
  }, []);

  return (
    <select
      onChange={(e: ChangeEvent<HTMLSelectElement>) =>
        changeModel(e.target.value)
      }
      className="select max-w-xs bg-base-300 xl:w-full w-1/3"
    >
      {models.map((model) => (
        <option key={model}>{model}</option>
      ))}
    </select>
  );
}

function AgentSelect(): JSX.Element {
  const [agents, setAgents] = useState<string[]>(INITIAL_AGENTS);
  useEffect(() => {
    fetchAgents().then((fetchedAgents) => {
      setAgents(fetchedAgents);
    });
  }, []);
  return (
    <select
      onChange={(e: ChangeEvent<HTMLSelectElement>) =>
        changeAgent(e.target.value)
      }
      className="select max-w-xs bg-base-300 xl:w-full w-1/3"
    >
      {agents.map((agent) => (
        <option key={agent}>{agent}</option>
      ))}
    </select>
  );
}

function BannerSettings(): JSX.Element {
  return (
    <div className="banner">
      <ModelSelect />
      <AgentSelect />
    </div>
  );
}

export default BannerSettings;
