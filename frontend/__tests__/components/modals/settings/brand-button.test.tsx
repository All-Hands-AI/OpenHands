import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, vi } from "vitest";
import { BrandButton } from "#/components/features/settings/brand-button";

describe("BrandButton", () => {
  const onClickMock = vi.fn();

  it("should call onClick when clicked", async () => {
    const user = userEvent.setup();
    render(
      <BrandButton type="button" variant="primary" onClick={onClickMock}>
        Test Button
      </BrandButton>,
    );

    await user.click(screen.getByText("Test Button"));
  });
});
