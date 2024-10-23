import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

interface ImagePreviewProps {
  src: string;
  onClose: () => void;
}

function ImagePreview({ src, onClose }: ImagePreviewProps) {
  return (
    <div data-testid="image-preview">
      <img role="img" src={src} alt="" />
      <button type="button" onClick={onClose}>
        Close
      </button>
    </div>
  );
}

describe("ImagePreview", () => {
  it("should render an image", () => {
    render(
      <ImagePreview src="https://example.com/image.jpg" onClose={vi.fn} />,
    );
    const img = screen.getByRole("img");

    expect(screen.getByTestId("image-preview")).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "https://example.com/image.jpg");
  });

  it("should call onClose when the close button is clicked", async () => {
    const user = userEvent.setup();
    const onCloseMock = vi.fn();
    render(
      <ImagePreview
        src="https://example.com/image.jpg"
        onClose={onCloseMock}
      />,
    );

    const closeButton = screen.getByRole("button");
    await user.click(closeButton);

    expect(onCloseMock).toHaveBeenCalledOnce();
  });
});
