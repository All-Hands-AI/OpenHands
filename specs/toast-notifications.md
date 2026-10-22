# Toast notification specs

### TN-001: Readable toast text in every theme

- [x] Success, warning, loading and error toasts shall draw their text in the `contrast` high-emphasis ink on the `--oh-color-tertiary` toast surface. The built-in palettes keep that pairing at 4.5:1 or better: white in dark palettes, dark ink in Light+ and Solarized Light. Error toasts keep the status-error icon as their error cue. Embedding roots may override `--oh-contrast`, and toasts follow the nearest `[data-agent-server-ui]` scope. Toast copy, icons, placement, duration and links are unchanged.
