# Home launcher specs

### HL-001: Readable Code/Automate mode toggle

- [x] The selected mode label, and an unselected label while hovered, shall use the `contrast` high-emphasis ink on the `--oh-interactive-hover` pill. The built-in palettes keep that pairing at 4.5:1 or better: white in dark palettes, dark ink in Light+ and Solarized Light. Embedding roots may override `--oh-contrast`, and the toggle follows the nearest `[data-agent-server-ui]` scope. Mode selection, keyboard and radio semantics, and the pill animation are unchanged.

### HL-002: Dismissible Recommended automations rail

- [x] Home's Recommended automations rail shall show an X named "Hide Recommended automations" in its header. On fine-pointer devices the X appears while the rail is hovered or holds keyboard focus; on touch and coarse-pointer devices it is always visible.
- [x] Clicking the X shall remove the whole rail from Home at once (heading, cards and bottom inset) and turn **Show Recommended automations** in Application settings off without a reload. Turning that switch back on shall restore the rail on the next Home render.
- [x] The X and the switch shall share one browser-scoped preference that defaults to shown and survives a reload. The rails in the automations empty state and the onboarding say-hello step shall never show the X and shall ignore the preference.
