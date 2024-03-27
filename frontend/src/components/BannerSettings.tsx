import React, { ChangeEvent } from "react";
import {
  AGENTS,
  MODELS,
  changeAgent,
  changeModel,
} from "../services/settingsService";
import "./BannerSettings.css";

function ModelSelect(): JSX.Element {
  return (
    <select
      onChange={(e: ChangeEvent<HTMLSelectElement>) =>
        changeModel(e.target.value)
      }
      className="model-select"
    >
      {MODELS.map((model) => (
        <option>{model}</option>
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
      className="agent-select"
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
