import type { Preview } from "@storybook/react-vite";
import "../index.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },

    a11y: {
      // 'todo' - show a11y violations in the test UI only
      test: "todo",
    },
  },
};

export default preview;
