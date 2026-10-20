# Git chip icons in light themes (#18657)

Before/after evidence for the workspace, branch, external-link and
workspace-mode chip icons. `before-*` was served from main (product source
identical to `79abd32d8`); `after-*` from this branch.

## Commands

```sh
export OH_VERIFY_RUN=$(control-openhands launch --new --print-run)   # once per checkout
control-openhands doctor
# <run>/private/home/.config/uv/uv.toml pins litellm (SDK#6088), then:
control-openhands restart
control-openhands llm preset deepseek && control-openhands onboard --skip
control-openhands fixture git-repo --name qa-repo
control-openhands fixture git-repo --name qa-gh --remote https://github.com/qa-example/qa-gh.git
control-openhands conversation start --workspace qa-repo --prompt "Reply with only the word OK. Do not run any tools." --wait
control-openhands conversation start --workspace qa-gh   --prompt "Reply with only the word OK. Do not run any tools." --wait
# For each of Light+, Solarized Light, OpenHands-Neutral (default):
control-openhands browser goto /settings/app
control-openhands browser choose 'testid=color-theme-input' "<theme>"
control-openhands browser goto /conversations/<id>      # desktop and `viewport phone` (390x844)
control-openhands browser eval "<getComputedStyle(svg).color vs nearest opaque background, WCAG ratio>"
control-openhands browser screenshot --feature F07.git-control-bar --name <tag>-<theme>-<viewport>
# GitHub-origin chip: hover the repo link so the external-link icon shows.
# Home composer: `workspace open <run>/workspace/qa-repo` shows the workspace-mode chip.
```

## Measured icon contrast

| Chip icon | Theme | Before | After |
|---|---|---|---|
| workspace + branch (conversation, desktop and 390x844) | Light+ | `#FFF` on `#FFF`, 1.00:1 | `rgb(31,31,31)` on `#FFF`, 16.48:1 |
| workspace + branch (conversation, desktop and 390x844) | Solarized Light | `#FFF` on `rgb(253,246,227)`, 1.08:1 | `rgb(0,43,54)`, 13.92:1 |
| workspace + branch (conversation, desktop and 390x844) | Default dark | `#FFF` on `rgb(24,24,24)`, 17.76:1 | unchanged, 17.76:1 |
| external link (GitHub chip, hover gradient end) | Light+ | `#FFF` on `rgb(229,229,229)`, 1.26:1 | 13.08:1 |
| external link (GitHub chip, hover gradient end) | Solarized Light | `#FFF` on `rgb(230,223,204)`, 1.33:1 | 11.29:1 |
| external link (GitHub chip, hover gradient end) | Default dark | `#FFF` on `rgb(49,49,49)`, 13.01:1 | unchanged, 13.01:1 |
| workspace-mode "Local Repo" (home composer) | Light+ | 1.00:1 | 16.48:1 |
| workspace-mode "Local Repo" (home composer) | Solarized Light | 1.08:1 | 13.92:1 |
| workspace-mode "Local Repo" (home composer) | Default dark | 17.76:1 | unchanged, 17.76:1 |

No chip icon in `chat-git-control-bar` or `home-git-control-bar-preview` has a
`color` attribute after the fix.
