#! /bin/bash

echo "🚀 Welcome to OpenHands! Let's get your development environment ready..."

# Install pre-commit package
echo "📦 Installing pre-commit to help maintain code quality..."
python -m pip install pre-commit

# Install pre-commit hooks if .git directory exists
if [ -d ".git" ]; then
    echo "🔧 Setting up pre-commit hooks to keep your code clean..."
    pre-commit install
    make install-pre-commit-hooks
    echo ""
    echo "🎉 Setup complete! Your OpenHands development environment is ready!"
    echo "💡 You can now start contributing to OpenHands. Happy coding! 🚀"
fi
