# Theme interaction contracts

### TI-001: Theme-aware keyboard focus
- [x] Backend connection tabs and guidance shall use the host-overridable focus role, preserving their outline geometry and keyboard behavior. Default focus colors shall reach 3:1 on base, modal, raised, and hovered neutral surfaces in all five themes.

### TI-002: Exported legacy drawer scrim
- [x] The SettingsMobileDrawer backdrop shall compile to 50% black opacity in Tailwind's supported CSS branches. Preserve close and navigation behavior; the current application uses the mobile settings hub rather than this exported legacy drawer.
