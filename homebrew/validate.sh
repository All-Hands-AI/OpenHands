#!/bin/bash
#
# Validation script for Homebrew formula setup
# This script checks that all necessary files are in place and properly formatted
#

set -e

echo "🔍 OpenHands Homebrew Formula Validation"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "homebrew" ]; then
    echo "❌ Error: homebrew/ directory not found!"
    echo "   Please run this script from the OpenHands repository root"
    exit 1
fi

echo "✅ Found homebrew/ directory"

# Check required files
REQUIRED_FILES=(
    "homebrew/openhands.rb"
    "homebrew/README.md"
    "homebrew/DEVELOPMENT.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Found $file"
    else
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

# Check formula syntax
echo ""
echo "📝 Checking formula syntax..."

if [ ! -f "homebrew/openhands.rb" ]; then
    echo "❌ Formula file not found!"
    exit 1
fi

# Basic Ruby syntax checks
if ! grep -q "class Openhands < Formula" homebrew/openhands.rb; then
    echo "❌ Formula class definition not found!"
    exit 1
fi
echo "✅ Formula class definition found"

if ! grep -q "def install" homebrew/openhands.rb; then
    echo "❌ Install method not found!"
    exit 1
fi
echo "✅ Install method found"

if ! grep -q "test do" homebrew/openhands.rb; then
    echo "❌ Test block not found!"
    exit 1
fi
echo "✅ Test block found"

# Check for required fields
if ! grep -q 'desc "' homebrew/openhands.rb; then
    echo "❌ Description not found!"
    exit 1
fi
echo "✅ Description found"

if ! grep -q 'homepage "' homebrew/openhands.rb; then
    echo "❌ Homepage not found!"
    exit 1
fi
echo "✅ Homepage found"

if ! grep -q 'license "' homebrew/openhands.rb; then
    echo "❌ License not found!"
    exit 1
fi
echo "✅ License found"

# Check for command wrappers
if ! grep -q 'bin/"oh"' homebrew/openhands.rb; then
    echo "❌ 'oh' command wrapper not found!"
    exit 1
fi
echo "✅ 'oh' command wrapper found"

if ! grep -q 'bin/"openhands"' homebrew/openhands.rb; then
    echo "❌ 'openhands' command wrapper not found!"
    exit 1
fi
echo "✅ 'openhands' command wrapper found"

# Check README content
echo ""
echo "📝 Checking README.md content..."

if ! grep -q "Installation" homebrew/README.md; then
    echo "❌ Installation section not found in README!"
    exit 1
fi
echo "✅ Installation section found"

if ! grep -q "brew install openhands" homebrew/README.md; then
    echo "❌ Installation command not found in README!"
    exit 1
fi
echo "✅ Installation command found"

# Check if main README was updated
echo ""
echo "📝 Checking main README.md..."

if ! grep -q "Homebrew" README.md; then
    echo "❌ Homebrew section not found in main README!"
    exit 1
fi
echo "✅ Homebrew section found in main README"

if ! grep -q "brew install openhands" README.md; then
    echo "❌ Homebrew installation command not found in main README!"
    exit 1
fi
echo "✅ Homebrew installation command found in main README"

# Check for oh command in README
if ! grep -q "oh" README.md; then
    echo "⚠️  Warning: 'oh' command not prominently featured in main README"
else
    echo "✅ 'oh' command mentioned in main README"
fi

# Summary
echo ""
echo "=========================================="
echo "✅ All validation checks passed!"
echo ""
echo "Next steps:"
echo "1. Test the formula locally:"
echo "   brew install --build-from-source ./homebrew/openhands.rb"
echo ""
echo "2. Test the commands:"
echo "   oh --help"
echo "   openhands --help"
echo ""
echo "3. Run brew tests:"
echo "   brew test openhands"
echo ""
echo "4. Audit the formula:"
echo "   brew audit ./homebrew/openhands.rb"
echo ""
echo "5. Commit and push the changes"
echo "=========================================="
