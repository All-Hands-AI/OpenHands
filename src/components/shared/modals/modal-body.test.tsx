import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  MODAL_MAX_WIDTH_VIEWPORT,
  MODAL_WIDTH_CLASS,
  ModalBody,
  type ModalWidth,
} from "./modal-body";

describe("ModalBody", () => {
  // Regression test for
  // https://github.com/OpenHands/OpenHands/issues/18432 — unlike the dialogs
  // that add the viewport cap by hand, the shared ModalBody used to render a
  // fixed width only (e.g. 520px for `md`), so on a 390px phone the dialog
  // overflowed the screen and its title and buttons were cut off.
  it("caps the rendered width to the viewport", () => {
    render(
      <ModalBody testID="modal-body" width="md">
        <span />
      </ModalBody>,
    );

    const body = screen.getByTestId("modal-body");

    // Fixed width is kept for desktop...
    expect(body.className).toContain(MODAL_WIDTH_CLASS.md);
    // ...but never exceeds 90vw, so 390px phone => at most 351px.
    expect(body.className).toContain(MODAL_MAX_WIDTH_VIEWPORT);
  });

  it("applies the viewport cap for every supported width", () => {
    const widths = Object.keys(MODAL_WIDTH_CLASS) as ModalWidth[];

    for (const width of widths) {
      const { unmount } = render(
        <ModalBody testID={`modal-body-${width}`} width={width}>
          <span />
        </ModalBody>,
      );

      expect(screen.getByTestId(`modal-body-${width}`).className).toContain(
        MODAL_MAX_WIDTH_VIEWPORT,
      );
      unmount();
    }
  });

  it("still preserves a caller-provided className", () => {
    render(
      <ModalBody testID="modal-body" className="mt-4">
        <span />
      </ModalBody>,
    );

    const body = screen.getByTestId("modal-body");

    expect(body.className).toContain("mt-4");
    expect(body.className).toContain(MODAL_MAX_WIDTH_VIEWPORT);
  });
});
