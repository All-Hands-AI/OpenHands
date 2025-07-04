# @openhands/ui

A modern React component library built with TypeScript and Tailwind CSS.

## Installation

Choose your preferred package manager:

```bash
# npm
npm install @openhands/ui

# yarn
yarn add @openhands/ui

# pnpm
pnpm add @openhands/ui

# bun
bun add @openhands/ui
```

## Quick Start

```tsx
import { Button, Typography } from "@openhands/ui";
import "@openhands/ui/styles";

function App() {
  return (
    <div>
      <Typography.H1>Hello World</Typography.H1>
      <Button variant="primary">Get Started</Button>
    </div>
  );
}
```

## Components

| Component         | Description                               |
| ----------------- | ----------------------------------------- |
| `Button`          | Interactive button with multiple variants |
| `Checkbox`        | Checkbox input with label support         |
| `Chip`            | Display tags or labels                    |
| `Divider`         | Visual separator                          |
| `Icon`            | Icon wrapper component                    |
| `Input`           | Text input field                          |
| `InteractiveChip` | Clickable chip component                  |
| `RadioGroup`      | Radio button group                        |
| `RadioOption`     | Individual radio option                   |
| `Scrollable`      | Scrollable container                      |
| `Toggle`          | Toggle switch                             |
| `Tooltip`         | Tooltip overlay                           |
| `Typography`      | Text components (H1-H6, Text, Code)       |

## Development

Use your preferred package manager to install dependencies and run the development server. We recommend using [Bun](https://bun.sh) for a fast development experience.

```bash
# Install dependencies
bun install

# Start Storybook
bun run dev

# Build package
bun run build
```

## License

MIT
