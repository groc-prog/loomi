# Development environment setup

Ready to write some code or fix a bug for **loomi**? This guide will help you get your local development environment ready so you can get started in a few minutes.

---

## 1. Prerequisites

Before you begin, make sure you have the following installed on your machine:
- **Python 3.13 or higher**
- **[Docker and Docker Compose](https://docs.docker.com/compose/)** for running Neo4j and Memgraph locally.
- **[Poetry](https://python-poetry.org/docs/#installation)** for managing dependencies.

---

## 2. Install dependencies and start containers

Poetry will automatically create an virtual environment and install `loomi` along with all development and testing dependencies. You can check the full [Poetry ](https://python-poetry.org/docs/basic-usage/) and [Docker Compose](https://docs.docker.com/compose/) documentation for more info.

Create a `.env` file containing the required variables:
- `NEO4J_AUTH`
- `MEMGRAPH_USER`
- `MEMGRAPH_PASSWORD`

> [!NOTE]
> You can choose any password you want. All containers are only running locally.

> [!WARNING]
> This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) to automatically generate change logs and determine release versions.

```bash
poetry install
poetry run pre-commit install
docker compose up -d
```

---

## 3. Verify by running tests

To ensure everything is installed correctly and all containers are running, you can run the test suite. For this, create a `.env.test` file and add the following environment variables:
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PWD`
- `MEMGRAPH_URI`
- `MEMGRAPH_USER`
- `MEMGRAPH_PWD`

> [!WARNING]
> The authentication details in `.env.test` must match the ones in the `.env` file!

```bash
poetry run pytest --envfile .env.test tests/
```

If all tests pass successfully, your environment is correctly set up and ready.

---

## 5. Create a Working Branch

Always write your code on a **feature branch** which is named appropriately to what you are implementing/fixing. Create a dedicated feature or bugfix branch (`feature/<your-fix-or-improvement>`) before making changes:

```bash
git checkout -b feature/your-feature-name
```

---

## Next Steps

- Made your changes? Check out the [Documentation Guide](./documentation-guide.md) if you need to update any docs.
- Ready to submit? Open a Pull Request on GitHub and describe your changes.
