import os

if os.getenv('K_SERVICE'):
    logconfig_dict = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {'json': {'()': 'app.common.logs.JsonFormatter'}},
        'handlers': {
            'stderr': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'stream': 'ext://sys.stderr',
            },
        },
        'root': {'level': 'INFO', 'handlers': ['stderr']},
        'loggers': {
            'gunicorn.error': {
                'level': 'INFO',
                'handlers': ['stderr'],
                'propagate': False,
            },
        },
    }
