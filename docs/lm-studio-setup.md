# LM-Studio Integration Guide

This guide explains how to set up and run OpenHands with LM-Studio for local LLM execution.

## Prerequisites

1. Install [LM-Studio](https://lmstudio.ai/)
2. Docker and Docker Compose
3. Python 3.10+

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
   
