import argparse
import uvicorn
from opendevin.server import listen

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Uvicorn server for OpenDevin app.")
    parser.add_argument("--llm-model", type=str, default="mistral:7b", help="Default chat/instruct model")
    parser.add_argument("--embeddings-model", type=str, default="llama2", help="Default embeddings model")
    parser.add_argument("--port", type=int, default=4173, help="Port for the server")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reloading of the server")
    parser.add_argument("--log-level", type=str, default="info", choices=["critical", "error", "warning", "info", "debug"], help="Log level for the server")
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Run Uvicorn server
    uvicorn.run("opendevin.server.listen:app",
        host="0.0.0.0",
        port=args.port,
        reload=True,
        log_level=args.log_level)
