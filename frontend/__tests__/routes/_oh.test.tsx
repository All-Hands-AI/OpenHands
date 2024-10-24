import { describe, it, test } from "vitest";

describe("frontend/routes/_oh", () => {
  describe("brand logo", () => {
    it.todo("should not do anything if the user is in the main screen");
    it.todo(
      "should be clickable and redirect to the main screen if the user is not in the main screen",
    );
  });

  describe("user menu", () => {
    it.todo("should open the user menu when clicked");

    describe("logged out", () => {
      it.todo("should display a placeholder");
      test.todo("the logout option in the user menu should be disabled");
    });

    describe("logged in", () => {
      it.todo("should display the user's avatar");
      it.todo("should log the user out when the logout option is clicked");
    });
  });

  describe("config", () => {
    it.todo("should open the config modal when clicked");
    it.todo(
      "should not save the config and close the config modal when the close button is clicked",
    );
    it.todo(
      "should save the config when the save button is clicked and close the modal",
    );
    it.todo("should warn the user about saving the config when in /app");
  });
});
