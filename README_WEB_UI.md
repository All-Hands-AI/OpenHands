# 🌐 OpenHands Termux Web UI

Modern, responsive web interface for OpenHands AI Assistant on Android/Termux.

## ✨ Features

### 🎯 Core Features
- **💬 Chat Interface**: Interactive chat with AI assistant
- **🖥️ Terminal**: Execute commands directly from web interface
- **📊 System Monitor**: Real-time system resource monitoring
- **⚙️ Settings**: Configure API keys, models, and parameters

### 🚀 Technical Features
- **📱 Mobile-First**: Optimized for Android devices
- **🌙 Dark Theme**: Easy on the eyes for long coding sessions
- **⚡ Real-time**: WebSocket connections for live updates
- **📴 PWA**: Install as Progressive Web App
- **🔄 Auto-refresh**: Automatic system monitoring updates
- **💾 Offline Support**: Service worker for offline functionality

### 🤖 AI Integration
- **🔑 Custom API Keys**: Support for any OpenAI-compatible API
- **🌐 Multiple Providers**: OpenAI, Anthropic, Google, Groq, Ollama
- **🎛️ Model Parameters**: Adjust temperature, max tokens, system prompt
- **📡 Streaming**: Real-time response streaming
- **💬 Chat History**: Persistent conversation history

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository (if not already done)
git clone https://github.com/mulkymalikuldhrs/OpenHands.git
cd OpenHands

# Switch to termux-version branch
git checkout termux-version

# Install web UI
./install_web_ui.sh
```

### 2. Start Web UI

```bash
# Start the web server
./start_web_ui.sh

# Access in browser
# Local: http://localhost:8000
# Network: http://YOUR_IP:8000
```

### 3. Configure API

1. Open web interface
2. Go to **Settings** tab
3. Select your AI provider
4. Enter API key and configure model
5. Test connection
6. Start chatting!

## 📱 Installation as PWA

### Android Chrome/Edge:
1. Open web UI in browser
2. Tap menu (⋮) → "Add to Home screen"
3. Confirm installation
4. Launch from home screen

### Features when installed:
- ✅ Full-screen experience
- ✅ App-like navigation
- ✅ Offline functionality
- ✅ Push notifications (future)

## 🛠️ Architecture

### Frontend (React + TypeScript)
```
termux_web_ui/
├── src/
│   ├── components/          # React components
│   │   ├── ChatInterface.tsx
│   │   ├── SettingsPanel.tsx
│   │   ├── SystemMonitor.tsx
│   │   └── TerminalPanel.tsx
│   ├── contexts/           # React contexts
│   │   ├── ConfigContext.tsx
│   │   └── WebSocketContext.tsx
│   ├── hooks/              # Custom hooks
│   ├── services/           # API services
│   ├── types/              # TypeScript types
│   └── utils/              # Utility functions
├── public/                 # Static assets
└── dist/                   # Built files
```

### Backend (FastAPI + Python)
```
termux_web_ui_server.py     # Main server
├── /api/chat              # Chat endpoints
├── /api/system            # System info & commands
├── /api/files             # File operations
├── /api/config            # Configuration
└── /ws                    # WebSocket connection
```

## 🔧 Configuration

### Server Configuration (`web_ui_config.json`)
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "auto_start": false
  },
  "ui": {
    "theme": "dark",
    "auto_refresh_interval": 5000,
    "max_chat_history": 100
  },
  "features": {
    "terminal": true,
    "system_monitor": true,
    "file_manager": true,
    "chat_streaming": true
  }
}
```

### Environment Variables
```bash
# Optional: Set default API configuration
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export DEFAULT_MODEL="gpt-3.5-turbo"
```

## 🎮 Usage Guide

### 💬 Chat Interface
- Type messages in the input field
- Press **Enter** to send (Shift+Enter for new line)
- Copy responses with copy button
- Clear chat history with Clear button
- Markdown and code syntax highlighting supported

### 🖥️ Terminal
- Execute any Termux command
- Command history with ↑/↓ arrows
- Copy/download command outputs
- Real-time command execution
- Common commands quick-access buttons

### 📊 System Monitor
- Real-time CPU, memory, disk usage
- Battery status (Android)
- Network statistics
- Auto-refresh every 5 seconds
- Manual refresh button

### ⚙️ Settings
- **Provider Selection**: Choose AI provider
- **API Configuration**: Set API key and base URL
- **Model Selection**: Choose AI model
- **Parameters**: Adjust temperature, max tokens
- **System Prompt**: Customize AI behavior
- **Connection Test**: Verify API settings

## 🔌 API Providers

### Supported Providers:

#### 🤖 OpenAI
```
Base URL: https://api.openai.com/v1
Models: gpt-3.5-turbo, gpt-4, gpt-4-turbo, gpt-4o
API Key: Required
```

#### 🧠 Anthropic Claude
```
Base URL: https://api.anthropic.com
Models: claude-3-sonnet, claude-3-haiku, claude-3-opus
API Key: Required
```

#### 🔍 Google Gemini
```
Base URL: https://generativelanguage.googleapis.com/v1beta
Models: gemini-pro, gemini-pro-vision
API Key: Required
```

#### ⚡ Groq
```
Base URL: https://api.groq.com/openai/v1
Models: mixtral-8x7b-32768, llama2-70b-4096
API Key: Required
```

#### 🏠 Ollama (Local)
```
Base URL: http://localhost:11434/v1
Models: llama2, codellama, mistral, neural-chat
API Key: Not required
```

## 🛠️ Development

### Prerequisites
- Node.js 18+
- Python 3.8+
- Termux environment

### Setup Development Environment
```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Start development server
npm run dev          # Frontend (port 3000)
python termux_web_ui_server.py --dev  # Backend (port 8000)
```

### Build for Production
```bash
# Build frontend
npm run build

# Start production server
python termux_web_ui_server.py
```

### Project Structure
```
OpenHands/
├── termux_web_ui/              # Frontend React app
│   ├── src/                    # Source code
│   ├── public/                 # Static assets
│   ├── dist/                   # Built files
│   └── package.json            # Dependencies
├── termux_web_ui_server.py     # Backend server
├── install_web_ui.sh           # Installation script
├── start_web_ui.sh             # Startup script
├── stop_web_ui.sh              # Stop script
└── web_ui_config.json          # Configuration
```

## 🚨 Troubleshooting

### Common Issues:

#### 🔌 Server Won't Start
```bash
# Check if port is in use
netstat -tulpn | grep :8000

# Kill existing process
pkill -f termux_web_ui_server

# Restart server
./start_web_ui.sh
```

#### 🌐 Can't Access from Other Devices
```bash
# Check firewall (if any)
# Ensure server is bound to 0.0.0.0
# Check your device's IP address
ip addr show
```

#### 🤖 API Connection Failed
- ✅ Verify API key is correct
- ✅ Check base URL format
- ✅ Test internet connection
- ✅ Try different model
- ✅ Check API provider status

#### 📱 PWA Installation Issues
- ✅ Use HTTPS or localhost
- ✅ Ensure manifest.json is accessible
- ✅ Check browser compatibility
- ✅ Clear browser cache

### Debug Mode
```bash
# Start server in debug mode
python termux_web_ui_server.py --dev

# Check logs
tail -f ~/openhands_web_ui_install.log
```

## 🔄 Updates

### Update Web UI
```bash
# Pull latest changes
git pull origin termux-version

# Rebuild UI
cd termux_web_ui
npm install
npm run build
cd ..

# Restart server
./stop_web_ui.sh
./start_web_ui.sh
```

## 📋 Management Commands

```bash
# Start web UI
./start_web_ui.sh

# Stop web UI
./stop_web_ui.sh

# Check status
pgrep -f termux_web_ui_server

# View logs
tail -f ~/openhands_web_ui_install.log

# Restart
./stop_web_ui.sh && ./start_web_ui.sh
```

## 🎯 Performance Tips

### 🚀 Optimize Performance:
- Use WiFi for better connectivity
- Close unused apps to free memory
- Enable auto-refresh only when needed
- Use appropriate model for your device
- Clear chat history periodically

### 🔋 Battery Optimization:
- Disable auto-refresh when not monitoring
- Use lower refresh intervals
- Close web UI when not in use
- Consider using local models (Ollama)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes to web UI
4. Test thoroughly on Android
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- 📖 Documentation: This README
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Contact: Create an issue for support

---

**🎉 Enjoy your AI-powered Android development experience with OpenHands Termux Web UI!**