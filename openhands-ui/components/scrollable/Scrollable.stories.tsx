import type { Meta, StoryObj } from "@storybook/react-vite";
import { Scrollable } from "./Scrollable";
import { Typography } from "../typography/Typography";

const meta = {
  title: "Components/Scrollable",
  component: Scrollable,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Scrollable>;

export default meta;

type Story = StoryObj<typeof meta>;

const text = `
      Vivamus fermentum metus eget aliquet sagittis. Quisque tempor velit id
      urna auctor, egestas venenatis leo accumsan. Vivamus quis turpis semper,
      volutpat odio vel, laoreet urna. Nunc vitae felis non lectus efficitur
      tristique nec ac leo. Phasellus libero risus, egestas non urna sit amet,
      ultricies venenatis enim. Proin in cursus est, vitae volutpat orci. Proin
      posuere, leo id placerat sodales, nunc risus egestas ex, non ultrices
      ipsum justo non metus. Quisque sit amet dapibus massa. Proin vel eros
      hendrerit libero rutrum posuere a eget enim. Donec mollis ultricies
      sodales. Curabitur sapien purus, faucibus ut aliquam sit amet, pulvinar
      accumsan massa. Duis gravida dapibus turpis, vitae euismod massa tristique
      non. Curabitur massa felis, rhoncus ac tellus nec, molestie aliquet dolor.
      Nunc et semper ligula, et lobortis dolor. Proin venenatis fermentum nibh.
      Etiam maximus rutrum leo, nec varius ipsum laoreet ut. Donec facilisis
      augue a massa ornare, eu mollis quam consectetur. Donec vitae diam lacus.
      Nullam vitae erat nec neque elementum fermentum. Pellentesque condimentum
      ac sem quis porta. Nam mattis vel nulla in venenatis. Nulla ac mattis
      ligula. Etiam fermentum, quam finibus euismod efficitur, magna ex luctus
      enim, quis eleifend risus leo non ex. Nunc aliquet laoreet nibh, quis
      fringilla lorem dapibus sit amet. Nullam ipsum libero, suscipit at massa
      quis, sagittis elementum magna. Pellentesque ac varius dolor, in molestie
      velit. Sed sagittis felis at velit tincidunt facilisis. Fusce et lacinia
      elit, ac mattis risus. Fusce mollis augue magna, in laoreet dui
      scelerisque at. Mauris facilisis rutrum elit ac facilisis. Morbi a
      fringilla velit. Ut id nulla sagittis, accumsan libero vel, placerat nisi.
      Etiam lacinia lectus orci, maximus tempus leo interdum at. Proin sapien
      est, pretium quis urna tempor, gravida convallis dolor. Maecenas eget
      lorem odio. Duis maximus diam id mauris cursus, ut tempus sapien
      tristique. Vestibulum ante ipsum primis in faucibus orci luctus et
      ultrices posuere cubilia curae; Aliquam fermentum, ipsum et consectetur
      blandit, nibh erat tempus justo, in aliquet ex mi in tortor. Nullam
      posuere tortor sed mattis dictum. Nam vel nulla ex. Aenean ac est nec
      tellus cursus semper id non est. Morbi placerat ex vel nibh fringilla,
      vitae porta velit consequat. Sed facilisis, lacus ultrices lobortis
      efficitur, odio augue sodales tortor, vel maximus velit purus quis nulla.
      Nullam malesuada accumsan augue id auctor.
`;

export const Vertical: Story = {
  args: {
    mode: "scroll",
    type: "vertical",
  },
  render: ({ mode, type }) => (
    <Scrollable type={type} mode={mode} className="h-64 max-w-128 p-4">
      <Typography.Text>{text}</Typography.Text>
    </Scrollable>
  ),
};

export const Horizontal: Story = {
  args: {
    mode: "scroll",
    type: "horizontal",
  },
  render: ({ mode, type }) => (
    <Scrollable type={type} mode={mode} className="max-h-32 w-64 p-4">
      <Typography.Text>{text}</Typography.Text>
    </Scrollable>
  ),
};
