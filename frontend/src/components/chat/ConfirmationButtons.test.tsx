import { describe } from "vitest";
import { userEvent } from "@testing-library/user-event";
import React from "react";
import { render, screen } from "@testing-library/react";
import ConfirmationButtons from "./ConfirmationButtons";
import AgentState from "#/types/AgentState";

describe("ConfirmationButtons", () => {
  // FIXME: mocked changeAgentState after its removal; need to update this test
  const changeAgentState = vi.fn();

  it("should change agent state appropriately on button click", async () => {
    const user = userEvent.setup();
    render(<ConfirmationButtons />);

    const confirmButton = screen.getByTestId("action-confirm-button");
    const rejectButton = screen.getByTestId("action-reject-button");

    await user.click(confirmButton);
    expect(changeAgentState).toHaveBeenCalledWith(AgentState.USER_CONFIRMED);

    await user.click(rejectButton);
    expect(changeAgentState).toHaveBeenCalledWith(AgentState.USER_REJECTED);
  });
});
