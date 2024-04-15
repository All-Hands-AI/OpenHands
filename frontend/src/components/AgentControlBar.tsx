import React, { useEffect } from "react";
import { Button, ButtonGroup, Tooltip } from "@nextui-org/react";
import { useSelector } from "react-redux";
import PauseIcon from "../assets/pause";
import PlayIcon from "../assets/play";
import AgentTaskAction from "../types/AgentTaskAction";
import { changeTaskState } from "../services/agentStateService";
import store, { RootState } from "../store";
import AgentTaskState from "../types/AgentTaskState";
import toast from "../utils/toast";
import ArrowIcon from "../assets/arrow";
import { clearMsgs } from "../services/session";
import { clearMessages } from "../state/chatSlice";

const TaskStateActionMap = {
  [AgentTaskAction.START]: AgentTaskState.RUNNING,
  [AgentTaskAction.PAUSE]: AgentTaskState.PAUSED,
  [AgentTaskAction.RESUME]: AgentTaskState.RUNNING,
  [AgentTaskAction.STOP]: AgentTaskState.STOPPED,
};

function AgentControlBar() {
  const { curTaskState } = useSelector((state: RootState) => state.agent);
  const [desiredState, setDesiredState] = React.useState(AgentTaskState.INIT);
  const [isRestart, setIsRestart] = React.useState(false);

  const Buttons = {
    [AgentTaskAction.RESTART]: {
      icon: <ArrowIcon />,
      tooltip: "Restart a new agent task",
    },
    [AgentTaskAction.PAUSE]: {
      icon: <PauseIcon />,
      tooltip: "Pause the agent task",
    },
    [AgentTaskAction.RESUME]: {
      icon: <PlayIcon />,
      tooltip: "Resume the agent task",
    },
  };

  const handleAction = (action: AgentTaskAction) => {
    let act = action;

    if (act === AgentTaskAction.RESTART) {
      setIsRestart(true);
      act = AgentTaskAction.STOP;
      clearMsgs().then().catch();
      store.dispatch(clearMessages());
    }

    setDesiredState(TaskStateActionMap[act]);
    changeTaskState(act);
  };

  useEffect(() => {
    if (curTaskState === desiredState) {
      if (isRestart) {
        setIsRestart(false);
        clearMsgs().then().catch();
        store.dispatch(clearMessages());
      }
      toast.info(`Task state is ${curTaskState}.`);
    } else if (curTaskState === AgentTaskState.RUNNING) {
      setDesiredState(AgentTaskState.RUNNING);
    }
  }, [curTaskState]);

  return (
    <div className="ml-5 mt-3">
      <ButtonGroup size="sm" variant="ghost">
        {Object.entries(Buttons).map(([key, item]) => (
          <Tooltip key={key} content={item.tooltip} closeDelay={100}>
            <Button
              isIconOnly
              aria-label={item.tooltip}
              onClick={() => handleAction(key as AgentTaskAction)}
            >
              {item.icon}
            </Button>
          </Tooltip>
        ))}
      </ButtonGroup>
    </div>
  );
}

export default AgentControlBar;
