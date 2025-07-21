#!/usr/bin/env python3
"""
Test script to generate a minimal Dockerfile for Ubuntu 24.04 to isolate the build issue.
"""

import sys
sys.path.append('.')
from openhands.runtime.utils.runtime_build import _generate_dockerfile

def create_minimal_dockerfile():
    """Create a minimal Dockerfile to test Ubuntu 24.04 build."""
    
    # Generate the full dockerfile
    dockerfile_content = _generate_dockerfile(
        base_image='ubuntu:24.04',
        extra_deps=None,
        enable_browser=True
    )
    
    # Write to file for inspection
    with open('/tmp/test_ubuntu_dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("Full Dockerfile written to /tmp/test_ubuntu_dockerfile")
    
    # Create a minimal version that only does the basic setup
    minimal_dockerfile = """FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Basic system update and Node.js installation (the suspected problem area)
RUN apt-get update && \\
    apt-get install -y --no-install-recommends \\
        wget curl ca-certificates sudo apt-utils git jq tmux build-essential ripgrep ffmpeg \\
        libgl1-mesa-glx \\
        libasound2-plugins libatomic1 && \\
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \\
    TZ=Etc/UTC DEBIAN_FRONTEND=noninteractive \\
        apt-get install -y --no-install-recommends nodejs \\
        python3.12 python3.12-venv python-is-python3 python3-pip && \\
    apt-get clean && \\
    rm -rf /var/lib/apt/lists/*

# Test Node.js installation
RUN node --version && npm --version

# Install poetry (without corepack)
RUN curl -fsSL --compressed https://install.python-poetry.org | python -

# Test poetry installation
RUN poetry --version

CMD ["/bin/bash"]
"""
    
    with open('/tmp/minimal_ubuntu_dockerfile', 'w') as f:
        f.write(minimal_dockerfile)
    
    print("Minimal Dockerfile written to /tmp/minimal_ubuntu_dockerfile")
    print("\nTo test locally, run:")
    print("docker build -f /tmp/minimal_ubuntu_dockerfile -t test-ubuntu .")

if __name__ == "__main__":
    create_minimal_dockerfile()