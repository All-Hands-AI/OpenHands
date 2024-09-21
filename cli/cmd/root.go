package cmd

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/user"
	"time"

	"github.com/spf13/cobra"

	"github.com/All-Hands-AI/OpenHands/cli/internal"
	"github.com/All-Hands-AI/OpenHands/cli/internal/browser"
)

const defaultCommand = "docker"

// validateFlags validates the flags passed to the command
// WORKSPACE -- [arg ...]
func validateFlags(cmd *cobra.Command, args []string) error {
	// validate command
	path, err := exec.LookPath(cfg.Command)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		getDocker()
		os.Exit(1)
	}
	cfg.Command = path

	// workspace is required
	if len(args) == 0 {
		return fmt.Errorf("workspace must be specified")
	}

	cfg.Workspace = args[0]
	cfg.Args = args[1:]

	// validate port
	if cfg.Port <= 0 || cfg.Port > 65535 {
		port, err := findFreePort()
		if err != nil {
			return err
		}
		cfg.Port = port
	}

	if dir, err := os.Getwd(); err != nil {
		return err
	} else {
		cfg.WorkDir = dir
	}

	env := map[string]string{}
	cfg.Env = env

	if err := buildArgs(&cfg); err != nil {
		return err
	}

	log.Printf("cfg: %v", cfg)

	return nil
}

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Version: internal.AppVersion,
	Use:     fmt.Sprintf("%s WORKSPACE ", internal.AppName),
	Short:   fmt.Sprintf("The official command-line interface for %s.", internal.AppTitle),
	Long: fmt.Sprintf(`OpenHands: Code Less, Make More

Welcome to OpenHands (formerly OpenDevin), a platform for software development agents powered by AI.

OpenHands agents can do anything a human developer can: modify code, run commands,
browse the web, call APIs, and yes—even copy code snippets from StackOverflow.

Learn more at %s.`, internal.SiteURL),
	Args: validateFlags,
	Run: func(cmd *cobra.Command, args []string) {
		err := runIt(&cfg)
		if err != nil {
			log.Fatal(err)
		}
	},
	CompletionOptions: cobra.CompletionOptions{
		DisableDefaultCmd: true,
	},
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

var cfg internal.Config

func init() {
	// load defaults from env
	model := os.Getenv("LLM_MODEL")
	apiKey := os.Getenv("LLM_API_KEY")

	// flags
	rootCmd.PersistentFlags().BoolP("help", "h", false, "Display help and exit")
	rootCmd.PersistentFlags().Bool("version", false, "Display version and exit")

	rootCmd.PersistentFlags().BoolVar(&cfg.Browse, "browse", true, fmt.Sprintf("Open %s UI in a browser", internal.AppTitle))

	rootCmd.PersistentFlags().IntVarP(&cfg.Port, "port", "p", 0, fmt.Sprintf("Port to use for the %s server. default auto select", internal.AppTitle))
	rootCmd.PersistentFlags().StringVar(&cfg.Image, "image", internal.Image, "Specify the OpenHands Docker image")
	rootCmd.PersistentFlags().StringVar(&cfg.Sandbox, "sandbox", internal.SandBox, "Specify the Sandbox Docker image")

	rootCmd.PersistentFlags().StringVar(&cfg.LLM.Model, "llm-model", model, "Specify the LLM model")
	rootCmd.PersistentFlags().StringVar(&cfg.LLM.APIKey, "llm-api-key", apiKey, "Specify the LLM API key")

	rootCmd.PersistentFlags().StringVar(&cfg.Command, "command", defaultCommand, "Specify the Docker command to use")

	rootCmd.PersistentFlags().MarkHidden("command")
}

func buildArgs(cfg *internal.Config) error {
	u, err := user.Current()
	if err != nil {
		return err
	}

	args := []string{
		"run",
		"-e", "SANDBOX_RUNTIME_CONTAINER_IMAGE=" + cfg.Sandbox,
		"-e", "SANDBOX_USER_ID=" + u.Uid,
		"-e", "WORKSPACE_MOUNT_PATH=" + cfg.Workspace,
		"-e", "LLM_API_KEY=" + cfg.LLM.APIKey,
		"-e", "LLM_MODEL=" + cfg.LLM.Model,
		"-v", "/var/run/docker.sock:/var/run/docker.sock",
		"-v", cfg.Workspace + ":/opt/workspace_base",
		"-p", fmt.Sprintf("%v:3000", cfg.Port),
		"--add-host", "host.docker.internal=host-gateway",
		"--name", "openhands-cli-" + time.Now().Format("20060102150405"),
	}

	xopts, xargs := splitBy(cfg.Args, "--")

	args = append(args, xopts...)
	args = append(args, cfg.Image)
	args = append(args, xargs...)

	// update args
	cfg.Args = args

	return nil
}

func runIt(cfg *internal.Config) error {
	if cfg.Browse {
		link := fmt.Sprintf("http://localhost:%v", cfg.Port)
		go openPage(link)
	}
	err := internal.Run(cfg)
	return err
}

func openPage(link string) {
	timeout := 120 * time.Second

	log.Printf("service url: %s", link)

	ready, err := pollPage(link, timeout)
	if err != nil {
		log.Printf("%v", err)
	}
	if ready {
		if !browser.Open(link) {
			log.Printf("failed to open %s", link)
		}
	}
}

func getDocker() {
	link := "https://docs.docker.com/get-started/get-docker/"
	fmt.Printf("Docker is required to run %s.\n", internal.AppTitle)
	fmt.Printf("Please visit %s for more info.\n", link)
	browser.Open(link)
}
