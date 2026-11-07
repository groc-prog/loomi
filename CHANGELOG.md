# CHANGELOG

<!-- version list -->

## v2.0.0-rc.1 (2026-11-07)

### Bug Fixes

- Allow to get root logger from logging helper, correct order_by parameter typing
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Client result access ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Compiled template expressions checks, compound optimizations for nested list paths
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Compiling of nested db functions ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Correctly check string values when serializing nested values
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Descriptor not returning correct path when accessing list field without indexes or operators
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Properly print entity properties ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Remove log ctx, fix config inheritance issues ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Serialization error when mapping graph with only relationships returned by query
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Serialization error when mapping graph with only relationships returned by query for sync result
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Typing for client args ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

### Documentation

- Add client, model and session/transaction/result docs
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Change tracker usage, examples and operation types
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Fix wrong model inheritance docs, typos ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Improved docs setup ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Logging and log usage ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Minor improvements, missing dev setup ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Refine documentation ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Remove additional separators ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Update logging docs, fix broken code snippets ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Updated documentation to cover all logic ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

### Features

- Add helper method for creating custom db functions
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Allow passing string name of field to set method
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Clean up error messages in query helper functions
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Cleanup, update query builders to new expression logic
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Improve change tracker public api ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Improved query api with more flexible expressions
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Log warning when registered model is being overwritten
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Remove neo4j specific model serialization in favor of pydantic serialization
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Remove unused alias model ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Rename classes, add better comments, add client config for throwing if model is not registered but
  attempting to transform ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Rewrite descriptors, expressions and db functions for better optimization for list operators
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Rewrite query api, update actions config and dependabot, update logging
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Support for projections with pydantic models in builder
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Support projections into pydantic model ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Trigger release ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Update how logs are emitted by different modules
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Wrap compound expression nested in other compound expressions in parenthesis to preserve logical
  order ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

### Performance Improvements

- Cache transformed query results to prevent parsing duplicate entities in results
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Improve checksum generation performance ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Move shared logic to session mixin, only build log args if log level enabled
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Move shared logic to transaction mixin, only build log args if log level enabled
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Nested field descriptor computation ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Optimizations when building change tracker queries
  ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))

- Optimize model checksum generation ([#10](https://github.com/groc-prog/loomi/pull/10),
  [`e96e15c`](https://github.com/groc-prog/loomi/commit/e96e15c71f1eab407ffdaa26481cf4050df83496))


## v1.2.0-rc.1 (2026-10-01)

### Features

- Trigger release
  ([`26d49fc`](https://github.com/groc-prog/loomi/commit/26d49fccb837ef0d97ceec12e5047ccbab583ef4))


## v1.1.0 (2026-10-01)

### Features

- Replace xxhash with hashlib ([#4](https://github.com/groc-prog/loomi/pull/4),
  [`0e8fcfe`](https://github.com/groc-prog/loomi/commit/0e8fcfe1dda6bb1e8be5860d1d76951993df3ce4))


## v1.0.0 (2026-05-24)

- Initial Release
