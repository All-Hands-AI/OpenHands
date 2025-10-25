class Openhands < Formula
  include Language::Python::Virtualenv

  desc "OpenHands CLI - AI-powered software development assistant"
  homepage "https://github.com/All-Hands-AI/OpenHands"
  url "https://github.com/All-Hands-AI/OpenHands/archive/refs/heads/main.tar.gz"
  version "1.0.2"
  license "MIT"
  head "https://github.com/All-Hands-AI/OpenHands.git", branch: "main"

  depends_on "python@3.12"

  def install
    # Create a virtualenv with Python 3.12
    venv = virtualenv_create(libexec, "python3.12")

    # Install the CLI package from the openhands-cli subdirectory
    # This will automatically install all dependencies including openhands-sdk,
    # openhands-tools, prompt-toolkit, typer, and their transitive dependencies
    cd "openhands-cli" do
      venv.pip_install Pathname.pwd
    end

    # Create the 'oh' wrapper script
    (bin/"oh").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/bin/python" -m openhands_cli.simple_main "$@"
    EOS

    # Make the wrapper executable
    chmod 0755, bin/"oh"

    # Create 'openhands' as the primary command that calls the installed script
    (bin/"openhands").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/bin/python" -m openhands_cli.simple_main "$@"
    EOS

    chmod 0755, bin/"openhands"
  end

  def caveats
    <<~EOS
      OpenHands CLI has been installed!

      You can now use it with the short command:
        oh

      Or the full name:
        openhands

      To get started:
        oh --help

      First-time setup:
        oh

      The CLI will guide you through initial configuration.

      Note: On first run, macOS may show a security warning.
      If this happens, go to System Settings > Privacy & Security
      and click "Open Anyway" to allow the application to run.

      Requirements:
      - Docker Desktop or OrbStack must be installed for full functionality
      - An OpenAI API key or other LLM provider API key will be needed
    EOS
  end

  test do
    # Test that the commands exist and are executable
    assert_predicate bin/"oh", :exist?
    assert_predicate bin/"openhands", :exist?

    # Test help output works
    output = shell_output("#{bin}/oh --help 2>&1", 0)
    assert_match "OpenHands", output
  end
end
