def config(file_name):
  return {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s | %(module)s] %(message)s",
                "datefmt": "%B %d, %Y %H:%M:%S %Z"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default"
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": file_name,
                "formatter": "default"
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]}
}