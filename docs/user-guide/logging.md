# Logging configurations

This section covers how `loomi` emits logs, how to control log verbosity, and how to inject context metadata (such as active models and operations) into your logs.


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
