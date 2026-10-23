# Development environment setup

Want to write some code or fix a bug in loomi? This guide helps you get your local development environment ready in a few minutes.

## 1. Prerequisites

Before you begin, make sure the following are installed on your machine:

- **Python 3.13 or higher**
- **[Docker and Docker Compose](https://docs.docker.com/compose/)** — for running Neo4j and Memgraph locally
- **[Poetry](https://python-poetry.org/docs/#installation)** — for managing dependencies

## 2. Install dependencies

Poetry automatically creates a virtual environment and installs loomi along with all development and testing dependencies. For more information, see the [Poetry basic usage](https://python-poetry.org/docs/basic-usage/) and [Docker Compose](https://docs.docker.com/compose/) documentation.

Create a `.env` file containing the required variables:

- `NEO4J_AUTH`
- `MEMGRAPH_USER`
- `MEMGRAPH_PASSWORD`

> [!NOTE]
> You can choose any password you want. All containers only run locally.

```bash
poetry install
poetry run pre-commit install
```

## 3. Verify by running tests

To ensure everything is installed correctly and all containers are running, run the test suite. Create a `.env.test` file and add the following environment variables:

> [!NOTE]
> You can also use the same `.env` file for both Docker Compose and Pytest, but you need to make sure the variables are defined!

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PWD`
- `MEMGRAPH_URI`
- `MEMGRAPH_USER`
- `MEMGRAPH_PWD`

> [!CAUTION]
> The authentication details in `.env.test` must match those in the `.env` file.

```bash
docker compose up -d
poetry run pytest --envfile .env.test tests/
```

If all tests pass, your environment is correctly set up and ready to use.

## 4. Create a working branch

> [!NOTE]
> This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) to automatically generate changelogs and determine release versions.

Always write your code on a **feature branch** with a name that reflects what you are implementing or fixing. Create a dedicated feature or bugfix branch before making changes:

```bash
git checkout -b feature/your-feature-name
```

## Next steps

- Made your changes? See the [Documentation Guide](./documentation-guide.md) if you need to update any docs.
- Ready to submit? Open a pull request on GitHub and describe your changes.
