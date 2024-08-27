import { describe, it } from "vitest";

describe("Home", () => {
  describe("TaskForm", () => {
    it.todo("should not render the submit button when text is empty");
    it.todo("should render the submit button when text is not empty");
    it.todo("should be able to submit the form with the enter key");
    it.todo(
      "should not be able to submit the form with the enter key when text is empty",
    );
    it.todo("should display an error if trying to submit no input");
  });

  describe("Loading a repo from GH", () => {
    it.todo("should display all the available repos");
    it.todo("should filter through the repos when typing");
    it.todo("should fetch a repo if it is not owned by the user");
  });
});
