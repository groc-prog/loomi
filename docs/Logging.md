# Logging

Loomi uses a namespaced logger which can be accessed and configured with the `loomi` namespace. By default, the logger is only configured with a single filter, which is used to add additional metadata to certain logs. This can be especially useful when you already use structured logging.


## Log levels

Loomi uses all default log levels defined in the [`logging` package](https://docs.python.org/3/library/logging.html). Logs are grouped into the following categories and levels:
- **ERROR:** Any error related logs. All errors which raise a exception do not log that exception, it is up to you to catch and log it.
- **WARNING:** _Nothing special about these._
- **INFO:** Reserved for queries and their parameters. All queries which are executed by the client are logged at this level.
- **DEBUG:** Internal information which can be used to debug stuff which might not work as expected. You should not need this most of the time.
