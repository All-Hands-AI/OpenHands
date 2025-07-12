import type { Meta, StoryObj } from "@storybook/react-vite";
import { Tabs } from "./Tabs";

const meta = {
  title: "Components/Tabs",
  component: Tabs,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Tabs>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Main: Story = {
  args: {
    children: null,
  },
  render: ({}) => (
    <Tabs>
      <Tabs.Item text="Overview" icon="HouseFill">
        Summary of data
      </Tabs.Item>
      <Tabs.Item text="Analytics" icon="BarChartFill">
        Traffic and metrics
      </Tabs.Item>
      <Tabs.Item text="Settings" icon="GearFill">
        Customize profile
      </Tabs.Item>
    </Tabs>
  ),
};
export const Scrollable: Story = {
  args: {
    children: null,
  },
  render: ({}) => (
    <div className="max-w-md">
      <Tabs>
        <Tabs.Item text="Overview" icon="HouseFill">
          Summary of data
        </Tabs.Item>
        <Tabs.Item text="Analytics" icon="BarChartFill">
          Traffic and metrics
        </Tabs.Item>
        <Tabs.Item text="Settings" icon="GearFill">
          Customize profile
        </Tabs.Item>
        <Tabs.Item text="Billing" icon="CreditCardFill">
          Manage invoices
        </Tabs.Item>
        <Tabs.Item text="Integrations" icon="PlugFill">
          Third-party services
        </Tabs.Item>
        <Tabs.Item text="Notifications" icon="BellFill">
          Set alert preferences
        </Tabs.Item>
        <Tabs.Item text="Reports" icon="FileEarmarkBarGraphFill">
          Generate PDF reports
        </Tabs.Item>
        <Tabs.Item text="Feedback" icon="ChatDotsFill">
          Leave your thoughts
        </Tabs.Item>
        <Tabs.Item text="Access Control" icon="ShieldLockFill">
          Manage roles and permissions
        </Tabs.Item>
        <Tabs.Item text="Activity Log" icon="ClockHistory">
          Track recent actions
        </Tabs.Item>
        <Tabs.Item text="Support" icon="LifePreserver">
          Get help and resources
        </Tabs.Item>
        <Tabs.Item text="API Keys" icon="KeyFill">
          Generate or revoke keys
        </Tabs.Item>
        <Tabs.Item text="Localization" icon="Translate">
          Language and region
        </Tabs.Item>
        <Tabs.Item text="Deployments" icon="CloudUploadFill">
          View deployment history
        </Tabs.Item>
        <Tabs.Item text="Audit Trail" icon="FileLockFill">
          Security and compliance logs
        </Tabs.Item>
      </Tabs>
    </div>
  ),
};
