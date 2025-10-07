import os
import warnings

import uvicorn


def main():
    # Suppress SyntaxWarnings from pydub.utils about invalid escape sequences
    warnings.filterwarnings('ignore', category=SyntaxWarning, module=r'pydub\.utils')

    # When LOG_JSON=1, configure Uvicorn to emit JSON logs for error/access
    log_config = None
    if os.getenv('LOG_JSON', '0') in ('1', 'true', 'True'):
        log_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                # Uvicorn mutates 'default' and 'access' to set use_colors; keep them present using Uvicorn formatters
                'default': {
                    '()': 'uvicorn.logging.DefaultFormatter',
                    'fmt': '%(levelprefix)s %(message)s',
                    'use_colors': None,
                },
                'access': {
                    '()': 'uvicorn.logging.AccessFormatter',
                    'fmt': '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
                    'use_colors': None,
                },
                # Actual JSON formatters used by handlers below
                'json': {
                    '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                    'fmt': '%(message)s %(levelname)s %(name)s %(asctime)s %(exc_info)s',
                },
                'json_access': {
                    '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                    'fmt': '%(message)s %(levelname)s %(name)s %(asctime)s %(client_addr)s %(request_line)s %(status_code)s',
                },
            },
            'handlers': {
                'default': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'json',
                    'stream': 'ext://sys.stdout',
                },
                'access': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'json_access',
                    'stream': 'ext://sys.stdout',
                },
            },
            'loggers': {
                'uvicorn': {
                    'handlers': ['default'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'uvicorn.error': {
                    'handlers': ['default'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'uvicorn.access': {
                    'handlers': ['access'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
            'root': {'level': 'INFO', 'handlers': ['default']},
        }

    uvicorn.run(
        'openhands.server.listen:app',
        host='0.0.0.0',
        port=int(os.environ.get('port') or '3000'),
        log_level='debug' if os.environ.get('DEBUG') else 'info',
        log_config=log_config,
        # If LOG_JSON enabled, force colors off; otherwise let uvicorn default
        use_colors=False if log_config else None,
    )


if __name__ == '__main__':
    main()
