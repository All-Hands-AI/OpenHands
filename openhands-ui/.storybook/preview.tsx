import type { Preview } from "@storybook/react-vite";
import "../index.css";
import { ToastManager } from "../components/toast/ToastManager";

const preview: Preview = {
  decorators: [
    (Story) => (
      <ToastManager>
        <div className="bg-light-neutral-950 h-full px-4 py-4 rounded-sm min-h-96 min-w-96 flex flex-row items-center justify-center">
          <Story />
        </div>
      </ToastManager>
    ),
  ],
  parameters: {
    backgrounds: {
      default: "light",
      values: [
        { name: "light", value: "#ffffff" },
        { name: "dark", value: "#1a1a1a" },
      ],
    },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
};

export default preview;
