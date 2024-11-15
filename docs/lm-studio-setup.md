# LM-Studio Integration Guide

This guide explains how to set up and run OpenHands with LM-Studio for local LLM execution.

## System Requirements

1. Hardware:
   - CPU: Modern multi-core processor
   - RAM: 16GB minimum (32GB recommended)
   - Storage: 10GB+ free space

2. Software:
   - Docker and Docker Compose
   - Python 3.12+
   - LM-Studio
   - C++ build tools (installed automatically in Docker)

## Prerequisites

1. Install [LM-Studio](https://lmstudio.ai/)
2. Docker and Docker Compose
3. Python 3.12+

## Setup Instructions

1. **Configure LM-Studio**:
   - Launch LM-Studio
   - Load your desired models (you'll need at least 3 models):
     - One for the Supervisor Agent (Server Settings -> Port: 1234)
     - One for OpenHands Instance 1 (Server Settings -> Port: 1235)
     - One for OpenHands Instance 2 (Server Settings -> Port: 1236)
   - For each model:
     - Click "Start Server"
     - Set the port as specified above
     - Enable local inference
     - Make sure "Allow all origins (CORS)" is enabled

2. **Start OpenHands Services**:
   
