#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '/workspace/OpenHands')

from openhands.runtime.utils.runtime_build import _generate_dockerfile, BuildFromImageType

# Test the Dockerfile generation
dockerfile_content = _generate_dockerfile(
    base_image='ubuntu:24.04',
    build_from=BuildFromImageType.SCRATCH,
    enable_browser=True
)

print("Generated Dockerfile:")
print("=" * 50)
print(dockerfile_content)
print("=" * 50)

# Check for the corepack issue
if 'corepack enable yarn &&' in dockerfile_content:
    print("❌ ERROR: Found 'corepack enable yarn &&' in the first RUN block!")
    # Find the line number
    lines = dockerfile_content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'corepack enable yarn &&' in line:
            print(f"   Line {i}: {line.strip()}")
else:
    print("✅ GOOD: No 'corepack enable yarn &&' found in problematic location")

# Check for the workaround
if 'ln -s "$(dirname $(which node))/corepack" /usr/local/bin/corepack' in dockerfile_content:
    print("✅ GOOD: Found corepack workaround")
else:
    print("❌ ERROR: Corepack workaround not found!")

# Check for separate corepack enable
if 'RUN corepack enable yarn' in dockerfile_content:
    print("✅ GOOD: Found separate 'RUN corepack enable yarn' command")
else:
    print("❌ ERROR: Separate 'RUN corepack enable yarn' command not found!")