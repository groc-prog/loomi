# loomi

[![CI](https://github.com/groc-prog/loomi/actions/workflows/ci.yml/badge.svg)](https://github.com/groc-prog/loomi/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/loomi)](https://pypi.org/project/loomi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A minimalistic Python Object-Graph Mapper designed to handle the most common tasks when working with **Neo4j** or **Memgraph**.

## Features

- **Hybrid Sync/Async Architecture:** Built around the driver provided by the [`neo4j package`](https://pypi.org/project/neo4j/), loomi supports both sync and async clients.
- **Dual-Database Support:** Compatibility with both Neo4j and Memgraph out of the box.
- **Type Safety:** Fully typed models and queries thanks to [`pydantic`](https://pydantic.dev/docs/).
- **Compatibility out of the box:** Drop-in replacement when you already use the driver provided by the [`neo4j package`](https://pypi.org/project/neo4j/). Enable additional features as required.

---

## Installation

Install via `pip` or your favorite package manager:
```bash
pip install loomi
```

Or with poetry:
```bash
poetry add loomi
```

## How to get started

> [!IMPORTANT]
> If you find any issues with this package or the documentation, feel free to [open a new issue](https://github.com/groc-prog/loomi/issues/new).

You can find documentation for everything this package provides [here](./docs/index.md).

Want to contribute a feature of bugfix? Check out the [contribution guide](./docs/contribution-guide/index.md).
