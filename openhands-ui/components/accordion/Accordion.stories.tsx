import type { Meta, StoryObj } from "@storybook/react-vite";
import { Accordion, type AccordionProps } from "./Accordion";
import { useArray } from "../../shared/hooks/use-array";
import { Typography } from "../typography/Typography";

const meta = {
  title: "Components/Accordion",
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta;

export default meta;

type Story = StoryObj<typeof meta>;

const AccordionComponent = ({ type }: { type: AccordionProps["type"] }) => {
  const [keys, { replace }] = useArray(["foo"]);
  return (
    <div className="w-96">
      <Accordion type={type} expandedKeys={keys} setExpandedKeys={replace}>
        <Accordion.Item
          value="foo"
          label="file.txt"
          icon={"FileEarmarkPlusFill"}
        >
          <Typography.Text>total 30</Typography.Text>
        </Accordion.Item>
        <Accordion.Item
          value="bar"
          label="foo.ext"
          icon={"FileEarmarkPlusFill"}
        >
          <Typography.Text>total 60</Typography.Text>
        </Accordion.Item>
        <Accordion.Item
          value="ipsum"
          label="very_very_long_file_name_v3.pdf"
          icon={"FileEarmarkPlusFill"}
        >
          <Typography.Text>total 90</Typography.Text>
        </Accordion.Item>
      </Accordion>
    </div>
  );
};

export const Multi: Story = {
  render: () => <AccordionComponent type="multi" />,
};

export const Single: Story = {
  render: () => <AccordionComponent type="single" />,
};
