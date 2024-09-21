package internal

const (
	AppTitle = "OpenHands Platform"
	AppName  = "openhands"
	SiteURL  = "https://docs.all-hands.dev/"
)

// the following variables are set at build time
var (
	AppVersion = "0.0.1" // Semver version
	AppOS      = "unknown"

	SandBox = "ghcr.io/all-hands-ai/runtime:0.9-nikolaik"
	Image   = "ghcr.io/all-hands-ai/openhands:0.9"
)

type Config struct {
	Browse bool

	Workspace string
	Port      int
	Image     string
	Sandbox   string

	Command string
	Args    []string
	WorkDir string
	Env     map[string]string

	LLM LLMConfig
}

type LLMConfig struct {
	Model  string
	APIKey string
}
