package internal

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"syscall"

	"github.com/creack/pty"
)

func Run(cfg *Config) error {
	if _, err := spawn(cfg.Command, cfg.Args, cfg.Env, cfg.WorkDir, true); err != nil {
		return err
	}

	return nil
}

func spawn(bin string, args []string, envMap map[string]string, workDir string, tty bool) (int, error) {
	toEnv := func() []string {
		var env []string
		for k, v := range envMap {
			env = append(env, fmt.Sprintf("%s=%s", k, v))
		}
		return env
	}

	cmd := exec.Command(bin, args...)
	cmd.Env = append(os.Environ(), toEnv()...)

	if workDir == "" {
		workDir = filepath.Dir(bin)
	}
	cmd.Dir = workDir

	var ptmx *os.File
	var err error

	if tty {
		ptmx, err = pty.Start(cmd)
		if err != nil {
			return 0, fmt.Errorf("failed to start PTY: %v", err)
		}
		defer ptmx.Close()

		go func() {
			_, _ = io.Copy(os.Stdout, ptmx)
		}()
	} else {
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
	}

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	done := make(chan error, 1)
	go func() {
		done <- cmd.Wait()
	}()

	select {
	case sig := <-sigs:
		if cmd.Process != nil {
			cmd.Process.Signal(sig)
		}
		return 0, fmt.Errorf("signal received: %v", sig)
	case err := <-done:
		if err != nil {
			return 0, err
		}
	}

	return cmd.Process.Pid, nil
}
