import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SettingsDropdown } from "#/components/features/settings/settings-dropdown";

describe("SettingsDropdown", () => {
  it("should render a dropdown with the provided options when the input is focused", async () => {
    const user = userEvent.setup();
    const options = [
      { label: "Option 1", value: "option1" },
      { label: "Option 2", value: "option2" },
      { label: "Option 3", value: "option3" },
    ];

    render(
      <SettingsDropdown
        testId="test-dropdown"
        label="Test Dropdown"
        options={options}
      />,
    );

    expect(screen.queryByTestId("dropdown")).not.toBeInTheDocument();

    const input = screen.getByTestId("test-dropdown");
    await user.click(input);

    const dropdown = screen.getByTestId("dropdown");
    expect(dropdown).toBeInTheDocument();

    const renderedOptions = within(dropdown).getAllByTestId("dropdown-option");

    expect(renderedOptions).toHaveLength(3);
    expect(renderedOptions[0]).toHaveTextContent("Option 1");
    expect(renderedOptions[1]).toHaveTextContent("Option 2");
    expect(renderedOptions[2]).toHaveTextContent("Option 3");
  });

  it("should close the dropdown when the input is blurred", async () => {
    const user = userEvent.setup();
    const options = [
      { label: "Option 1", value: "option1" },
      { label: "Option 2", value: "option2" },
      { label: "Option 3", value: "option3" },
    ];

    render(
      <SettingsDropdown
        testId="test-dropdown"
        label="Test Dropdown"
        options={options}
      />,
    );

    const input = screen.getByTestId("test-dropdown");
    await user.click(input);

    const dropdown = screen.getByTestId("dropdown");
    expect(dropdown).toBeInTheDocument();

    await user.click(document.body);

    expect(screen.queryByTestId("dropdown")).not.toBeInTheDocument();
  });

  it("should render the selected option when an option is selected from the dropdown and close the dropdown", async () => {
    const user = userEvent.setup();
    const options = [
      { label: "Option 1", value: "option1" },
      { label: "Option 2", value: "option2" },
      { label: "Option 3", value: "option3" },
    ];

    render(
      <SettingsDropdown
        testId="test-dropdown"
        label="Test Dropdown"
        options={options}
      />,
    );

    const input = screen.getByTestId("test-dropdown");
    await user.click(input);

    const dropdown = screen.getByTestId("dropdown");
    expect(dropdown).toBeInTheDocument();

    const option1 = screen.getByText("Option 1");
    await user.click(option1);

    expect(screen.getByTestId("test-dropdown")).toHaveValue("Option 1");
    expect(screen.queryByTestId("dropdown")).not.toBeInTheDocument();
  });

  it("should be able to filter the options by typing in the input field", async () => {
    const user = userEvent.setup();
    const options = [
      { label: "myOption 1", value: "option1" },
      { label: "myOption 2", value: "option2" },
      { label: "Option 3", value: "option3" },
    ];

    render(
      <SettingsDropdown
        testId="test-dropdown"
        label="Test Dropdown"
        options={options}
      />,
    );

    const input = screen.getByTestId("test-dropdown");
    await user.click(input);
    await user.type(input, "my");

    expect(input).toHaveValue("my");

    const dropdown = screen.getByTestId("dropdown");
    expect(dropdown).toBeInTheDocument();

    const filteredOptions = within(dropdown).getAllByTestId("dropdown-option");

    expect(filteredOptions).toHaveLength(2);
    expect(filteredOptions[0]).toHaveTextContent("myOption 1");
    expect(filteredOptions[1]).toHaveTextContent("myOption 2");

    await user.clear(input);
    await user.type(input, "3");

    expect(input).toHaveValue("3");

    const updatedDropdown = screen.getByTestId("dropdown");
    expect(updatedDropdown).toBeInTheDocument();

    const updatedOptions =
      within(updatedDropdown).getAllByTestId("dropdown-option");

    expect(updatedOptions).toHaveLength(1);
    expect(updatedOptions[0]).toHaveTextContent("Option 3");
  });

  it("should show all options after selecting an option and then opening the dropdown again", async () => {
    const user = userEvent.setup();
    const options = [
      { label: "myOption 1", value: "option1" },
      { label: "Option 2", value: "option2" },
      { label: "Option 3", value: "option3" },
    ];

    render(
      <SettingsDropdown
        testId="test-dropdown"
        label="Test Dropdown"
        options={options}
      />,
    );

    const input = screen.getByTestId("test-dropdown");
    await user.click(input);
    await user.type(input, "my");

    const dropdown = screen.getByTestId("dropdown");
    expect(dropdown).toBeInTheDocument();

    const option1 = screen.getByText("myOption 1");
    await user.click(option1);

    expect(screen.getByTestId("test-dropdown")).toHaveValue("myOption 1");
    expect(screen.queryByTestId("dropdown")).not.toBeInTheDocument();

    await user.click(input);

    const updatedDropdown = screen.getByTestId("dropdown");
    expect(updatedDropdown).toBeInTheDocument();

    const updatedOptions =
      within(updatedDropdown).getAllByTestId("dropdown-option");

    expect(updatedOptions).toHaveLength(3);
    expect(updatedOptions[0]).toHaveTextContent("myOption 1");
    expect(updatedOptions[1]).toHaveTextContent("Option 2");
    expect(updatedOptions[2]).toHaveTextContent("Option 3");
  });

  it("should render a 'No options found' message if no options match the input value", async () => {
    const user = userEvent.setup();
    const options = [
      { label: "myOption 1", value: "option1" },
      { label: "Option 2", value: "option2" },
      { label: "Option 3", value: "option3" },
    ];

    const { rerender } = render(
      <SettingsDropdown
        testId="test-dropdown"
        label="Test Dropdown"
        options={options}
      />,
    );

    const input = screen.getByTestId("test-dropdown");
    await user.click(input);
    await user.type(input, "myOption 4");

    let dropdown = screen.getByTestId("dropdown");
    expect(dropdown).toBeInTheDocument();

    let noOptionsFound = within(dropdown).getByText("No options found");
    expect(noOptionsFound).toBeInTheDocument();

    rerender(
      <SettingsDropdown
        testId="test-dropdown"
        label="Test Dropdown"
        options={[]}
      />,
    );

    await user.click(input);

    dropdown = screen.getByTestId("dropdown");
    expect(dropdown).toBeInTheDocument();

    noOptionsFound = within(dropdown).getByTestId("no-options");

    expect(noOptionsFound).toBeInTheDocument();
    expect(noOptionsFound).toHaveTextContent("No options found");
  });
});
