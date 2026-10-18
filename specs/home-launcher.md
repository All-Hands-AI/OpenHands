# Home launcher specs

### HL-001: Readable Code/Automate mode toggle

- [x] The selected mode label, and an unselected label while hovered, shall use the `contrast` high-emphasis ink on the `--oh-interactive-hover` pill. The built-in palettes keep that pairing at 4.5:1 or better: white in dark palettes, dark ink in Light+ and Solarized Light. Embedding roots may override `--oh-contrast`, and the toggle follows the nearest `[data-agent-server-ui]` scope. Mode selection, keyboard and radio semantics, and the pill animation are unchanged.
