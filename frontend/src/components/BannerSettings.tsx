import React, { ChangeEvent, useEffect, useState } from "react";
import {
  AGENTS,
  INITIAL_MODELS,
  changeAgent,
  changeModel,
  fetchModels,
} from "../services/settingsService";
import "./BannerSettings.css";

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
  return (
    <select
      onChange={(e: ChangeEvent<HTMLSelectElement>) =>
        changeAgent(e.target.value)
      }
      className="select max-w-xs bg-base-300 xl:w-full w-1/3"
    >
      {AGENTS.map((agent) => (
        <option>{agent}</option>
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
