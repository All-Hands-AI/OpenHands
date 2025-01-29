import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ConnectionStatusModal } from "../connection-status-modal";
import { BaseModal } from "../base-modal/base-modal";
import { vi } from "vitest";

vi.mock("../base-modal/base-modal", () => ({
  BaseModal: ({ children, isOpen }: { children: React.ReactNode; isOpen: boolean }) => (
    isOpen ? <div>{children}</div> : null
  ),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key === "MODAL$UNSTABLE_CONNECTION" ? "Connection is unstable, attempting to reconnect..." : key,
  }),
}));

describe("ConnectionStatusModal", () => {
  it("should show modal when connection is unstable", () => {
    render(<ConnectionStatusModal isOpen={true} />);
    expect(
      screen.getByText("Connection is unstable, attempting to reconnect...")
    ).toBeInTheDocument();
  });

  it("should not show modal when connection is stable", () => {
    render(<ConnectionStatusModal isOpen={false} />);
    expect(
      screen.queryByText("Connection is unstable, attempting to reconnect...")
    ).not.toBeInTheDocument();
  });
});
