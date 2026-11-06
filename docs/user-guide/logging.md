# Logging configuration

Loomi uses Python's standard `logging` module. It leaves handlers and formatters to your application, so you can set logging up the way you prefer. For example, this shows informational messages from Loomi and other loggers:

```python
import logging

logging.basicConfig(level=logging.INFO)
```

## Logger names and levels

Loomi writes messages under the `loomi` logger. These child loggers help you narrow down what you see:

- `loomi.driver` covers client, session, transaction, and result activity
- `loomi.change_tracker` covers change tracker operations
- `loomi.model` covers model operations
- `loomi.query_api` covers query compilation and builder activity

At `INFO` level, the driver logger reports connection checks and query text with its parameters. If you want more detail about Loomi's work and query compilation, set the logger to `DEBUG`:

```python
logging.getLogger("loomi").setLevel(logging.DEBUG)
```

Your handlers and logging setup also affect which messages appear. Choose levels and destinations that fit your application.

> [!WARNING]
> Query logs can include parameter values. Be careful not to expose passwords, personal details, or other sensitive information in collected logs.
