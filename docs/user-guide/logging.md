# Logging configurations

This section covers how `loomi` emits logs, how to control log verbosity, and how to inject context metadata (such as active models and operations) into your logs.

---

## Logger namespaces & levels

`loomi` follows standard Python library guidelines. This means it adds **no handler and does not modify the root logger**. Instead, we use namespaced loggers for different parts of the application, allowing you to control different parts of the package logs independently:

- **`loomi`**: Root namespace for all loomi logs.
- **`loomi.driver`**: Client, session and transactions.
- **`loomi.change_tracker`**: Change tracking operations (inserts, updates, flushes).
- **`loomi.model`**: Model (de)serialization.
- **`loomi.query_api`**: Query compilation and builders.

Different log levels also map to different events from the package:

- **`debug`**: Debug logs and internal operations.
- **`info`**: Server connection and queries.
- **`warning`**: Duplicate setting definitions, recoverable issues during serialization, etc.
- **`error`**: Unrecoverable errors.

---

## Context enrichment (`LogContextFilter`)

During execution, `loomi` tracks internal state (like model identifiers, change change tracker operations and more) using `contextvars`. You can opt into this by registering `LogContextFilter` from the `loomi.logger` module on your logger.

```python
import logging
from loomi.logging import LogContextFilter

# 1. Get the loomi logger namespace
logger = logging.getLogger("loomi")
logger.setLevel(logging.INFO)

# 2. Create a logging handler
handler = logging.StreamHandler()

# 3. Include loomi context keys in your format string
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [Model: %(model_name)s] [Op: %(operation)s] - %(message)s"
)
handler.setFormatter(formatter)

# 4. Attach the optional context filter
handler.addFilter(LogContextFilter())
logger.addHandler(handler)
```
