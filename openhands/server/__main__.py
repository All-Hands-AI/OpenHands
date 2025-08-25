import os
import warnings

import uvicorn


def main():
    # Suppress SyntaxWarnings from pydub.utils about invalid escape sequences
    warnings.filterwarnings('ignore', category=SyntaxWarning, module=r'pydub\.utils')

    uvicorn.run(
        'openhands.server.listen:app',
        host='0.0.0.0',
        port=int(os.environ.get('port') or '3000'),
        log_level='debug' if os.environ.get('DEBUG') else 'info',
    )


if __name__ == '__main__':
    main()
