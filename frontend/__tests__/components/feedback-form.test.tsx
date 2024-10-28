import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FeedbackForm } from "#/components/feedback-form";

describe("FeedbackForm", () => {
  const user = userEvent.setup();
  const onSubmitMock = vi.fn();
  const onCloseMock = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render correctly", () => {
    render(<FeedbackForm onSubmit={onSubmitMock} onClose={onCloseMock} />);

    screen.getByLabelText("Email");
    screen.getByLabelText("Private");
    screen.getByLabelText("Public");

    screen.getByRole("button", { name: "Submit" });
    screen.getByRole("button", { name: "Cancel" });
  });

  it("should switch between private and public permissions", async () => {
    render(<FeedbackForm onSubmit={onSubmitMock} onClose={onCloseMock} />);
    const privateRadio = screen.getByLabelText("Private");
    const publicRadio = screen.getByLabelText("Public");

    expect(privateRadio).toBeChecked(); // private is the default value
    expect(publicRadio).not.toBeChecked();

    await user.click(publicRadio);
    expect(publicRadio).toBeChecked();
    expect(privateRadio).not.toBeChecked();

    await user.click(privateRadio);
    expect(privateRadio).toBeChecked();
    expect(publicRadio).not.toBeChecked();
  });

  it("should call onSubmit when the form is submitted", async () => {
    render(<FeedbackForm onSubmit={onSubmitMock} onClose={onCloseMock} />);
    const email = screen.getByLabelText("Email");

    await user.type(email, "test@test.test");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(onSubmitMock).toHaveBeenCalledWith("private", "test@test.test"); // private is the default value
  });

  it("should not call onSubmit when the email is invalid", async () => {
    render(<FeedbackForm onSubmit={onSubmitMock} onClose={onCloseMock} />);
    const email = screen.getByLabelText("Email");
    const submitButton = screen.getByRole("button", { name: "Submit" });

    await user.click(submitButton);

    expect(onSubmitMock).not.toHaveBeenCalled();

    await user.type(email, "test");
    await user.click(submitButton);

    expect(onSubmitMock).not.toHaveBeenCalled();
  });

  it("should submit public permissions when the public radio is checked", async () => {
    render(<FeedbackForm onSubmit={onSubmitMock} onClose={onCloseMock} />);
    const email = screen.getByLabelText("Email");
    const publicRadio = screen.getByLabelText("Public");

    await user.type(email, "test@test.test");
    await user.click(publicRadio);
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(onSubmitMock).toHaveBeenCalledWith("public", "test@test.test");
  });

  it("should call onClose when the close button is clicked", async () => {
    render(<FeedbackForm onSubmit={onSubmitMock} onClose={onCloseMock} />);
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onSubmitMock).not.toHaveBeenCalled();
    expect(onCloseMock).toHaveBeenCalled();
  });

  it("should disable the buttons if isSubmitting is true", () => {
    const { rerender } = render(
      <FeedbackForm onSubmit={onSubmitMock} onClose={onCloseMock} />,
    );
    const submitButton = screen.getByRole("button", { name: "Submit" });
    const cancelButton = screen.getByRole("button", { name: "Cancel" });

    expect(submitButton).not.toBeDisabled();
    expect(cancelButton).not.toBeDisabled();

    rerender(
      <FeedbackForm
        onSubmit={onSubmitMock}
        onClose={onCloseMock}
        isSubmitting
      />,
    );
    expect(submitButton).toBeDisabled();
    expect(cancelButton).toBeDisabled();
  });
});
