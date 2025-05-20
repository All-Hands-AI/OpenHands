import os

import uvicorn


def main():
    uvicorn.run(
        'openhands.server.listen:app',
        host='0.0.0.0',
        port=int(os.environ.get('port') or '3000'),
        log_level='debug' if os.environ.get('DEBUG') else 'info',
    )


if __name__ == '__main__':
    main()
