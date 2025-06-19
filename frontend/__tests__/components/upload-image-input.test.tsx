import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { UploadImageInput } from "#/components/features/images/upload-image-input";

describe("UploadImageInput", () => {
  const user = userEvent.setup();
  const onUploadMock = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render an input", () => {
    render(<UploadImageInput onUpload={onUploadMock} />);
    expect(screen.getByTestId("upload-image-input")).toBeInTheDocument();
  });

  it("should call onUpload when a file is selected", async () => {
    render(<UploadImageInput onUpload={onUploadMock} />);

    const file = new File(["(⌐□_□)"], "chucknorris.png", { type: "image/png" });
    const input = screen.getByTestId("upload-image-input");

    await user.upload(input, file);

    expect(onUploadMock).toHaveBeenNthCalledWith(1, [file]);
  });

  it("should call onUpload when multiple files are selected", async () => {
    render(<UploadImageInput onUpload={onUploadMock} />);

    const files = [
      new File(["(⌐□_□)"], "chucknorris.png", { type: "image/png" }),
      new File(["(⌐□_□)"], "chucknorris2.png", { type: "image/png" }),
    ];
    const input = screen.getByTestId("upload-image-input");

    await user.upload(input, files);

    expect(onUploadMock).toHaveBeenNthCalledWith(1, files);
  });

  it("should render custom labels", () => {
    const { rerender } = render(<UploadImageInput onUpload={onUploadMock} />);
    expect(screen.getByTestId("default-label")).toBeInTheDocument();

    function CustomLabel() {
      return <span>Custom label</span>;
    }
    rerender(
      <UploadImageInput onUpload={onUploadMock} label={<CustomLabel />} />,
    );

    expect(screen.getByText("Custom label")).toBeInTheDocument();
    expect(screen.queryByTestId("default-label")).not.toBeInTheDocument();
  });
});
