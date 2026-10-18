import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DetailHeader } from "#/components/features/automations/detail/detail-header";
import { I18nKey } from "#/i18n/declaration";
import type { Automation } from "#/types/automation";

const disabledAutomation: Automation = {
  id: "auto-1",
  name: "Daily digest",
  prompt: "Summarize",
  trigger: {
    type: "cron",
    schedule: "0 9 * * *",
    schedule_human: "Daily at 09:00",
  },
  enabled: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function renderHeader(
  props: Partial<React.ComponentProps<typeof DetailHeader>> = {},
) {
  return render(
    <DetailHeader
      automation={disabledAutomation}
      onToggle={vi.fn()}
      onDelete={vi.fn()}
      onExport={vi.fn()}
      onDownloadTarball={vi.fn()}
      {...props}
    />,
  );
}

describe("DetailHeader — status badge", () => {
  it("labels draft automations as draft instead of inactive", () => {
    renderHeader({
      automation: { ...disabledAutomation, state: "DRAFT" },
    });

    expect(screen.getByTestId("active-status-badge-draft")).toHaveTextContent(
      I18nKey.AUTOMATIONS$DETAIL$DRAFT,
    );
    expect(
      screen.queryByTestId("active-status-badge-inactive"),
    ).not.toBeInTheDocument();
  });
});

describe("DetailHeader — enabled toggle gating", () => {
  it("hides the switch and Turn on when canToggle is false but keeps Delete", async () => {
    // Arrange — a manager who did not create this disabled automation.
    const user = userEvent.setup();
    renderHeader({ canManage: true, canToggle: false });

    // Act
    await user.click(screen.getByLabelText(I18nKey.AUTOMATIONS$ACTIONS_MENU));

    // Assert
    expect(screen.queryByRole("switch")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: I18nKey.AUTOMATIONS$TURN_ON }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: I18nKey.AUTOMATIONS$DELETE }),
    ).toBeInTheDocument();
  });

  it("follows canManage for the switch when canToggle is omitted", () => {
    // Arrange / Act
    renderHeader({ canManage: true });

    // Assert
    expect(
      screen.getByRole("switch", { name: I18nKey.AUTOMATIONS$TURN_ON }),
    ).toBeInTheDocument();
  });
});

describe("DetailHeader — phone layout and responsive wrapping", () => {
  it("stacks on mobile viewports with min-w-0 title and wrapping action row", () => {
    renderHeader({
      automation: {
        ...disabledAutomation,
        name: "QA_Inert_Event_Detail",
        enabled: true,
      },
      onRunNow: vi.fn(),
      canManage: true,
      canToggle: true,
    });

    const heading = screen.getByRole("heading", {
      name: "QA_Inert_Event_Detail",
    });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveClass("break-words");

    const titleContainer = heading.parentElement;
    expect(titleContainer).toHaveClass("min-w-0");

    const switchControl = screen.getByRole("switch");
    const actionContainer = switchControl.parentElement;
    expect(actionContainer).toHaveClass("flex-wrap");

    // The row containing title and action controls must stack below `sm`
    const headerRow = titleContainer?.parentElement;
    expect(headerRow).toHaveClass("flex-col");
    expect(headerRow).toHaveClass("sm:flex-row");
    expect(headerRow).toHaveClass("sm:justify-between");
  });

  it("renders controls correctly with short names and partial action items", () => {
    renderHeader({
      automation: {
        ...disabledAutomation,
        name: "QA",
        enabled: false,
      },
      canManage: false,
      canToggle: false,
    });

    const heading = screen.getByRole("heading", { name: "QA" });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveClass("break-words");
    expect(
      screen.getByTestId("active-status-badge-inactive"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(I18nKey.AUTOMATIONS$ACTIONS_MENU),
    ).toBeInTheDocument();
  });
});

