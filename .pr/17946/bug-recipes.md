# Frozen root runtime regression recipes

### Local terminal directory regression

Launch with `--unprepared-tmux` to leave the run-owned short `TMUX_TMPDIR`
absent before the real npm launcher starts. This preserves an explicit user
override while avoiding the test harness masking the directory-creation defect.

```sh known-bug F26.tmux-directory once
control-openhands assert --field directoryExists --equals true --bug-shows false -- fixture tmux-directory # bug
```

