# Logging configuration

This section covers how loomi emits logs and how to control log verbosity.

## Logger namespaces and levels

loomi follows standard Python library guidelines. This means it **adds no handlers and does not modify the root logger**. Instead, loomi uses namespaced loggers for different parts of the application, allowing you to control the log output of different parts of the package independently:

- **`loomi`**: Root namespace for all loomi logs.
- **`loomi.driver`**: Clients, sessions, and transactions.
- **`loomi.change_tracker`**: Change tracking operations (inserts, updates, flushes).
- **`loomi.model`**: Model (de)serialization.
- **`loomi.query_api`**: Query compilation and builders.

Log levels map to different kinds of events emitted by the package:

- **`debug`**: Debug logs and internal operations.
- **`info`**: Server connection and queries.
- **`warning`**: Duplicate setting definitions, recoverable issues during serialization, and similar conditions.
- **`error`**: Unrecoverable errors.

```python
import logging
from loomi.logger import get_logger

# Enable debug logs for the whole package
getLogger().setLevel(logging.DEBUG)

# Or enable them for a single namespace only
getLogger("change_tracker").setLevel(logging.DEBUG)
```
