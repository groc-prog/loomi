# Development environment setup

Ready to write code or fix a bug in loomi? Follow these steps to get your local development environment set up.

## 1. Prerequisites

Before you start, install these tools:

- **Python 3.13 or higher**
- **[Docker and Docker Compose](https://docs.docker.com/compose/)**, so you can run Neo4j and Memgraph locally
- **[Poetry](https://python-poetry.org/docs/#installation)**, to manage project dependencies

## 2. Install dependencies

Poetry creates a virtual environment for you and installs loomi with its development and testing dependencies. If you are new to Poetry or Docker Compose, their [basic usage guide](https://python-poetry.org/docs/basic-usage/) and [Compose documentation](https://docs.docker.com/compose/) are good references.

Create a `.env` file and add these variables:

- `NEO4J_AUTH`
- `MEMGRAPH_USER`
- `MEMGRAPH_PASSWORD`

> [!NOTE]
> Choose any passwords you like. These containers run only on your local machine.

```bash
poetry install
poetry run pre-commit install
```

## 3. Verify by running tests

Now you can check that the installation works and the containers are running. Create a `.env.test` file with these environment variables:

> [!NOTE]
> You can use one `.env` file for Docker Compose and Pytest. Just make sure it defines every variable both tools need.

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PWD`
- `MEMGRAPH_URI`
- `MEMGRAPH_USER`
- `MEMGRAPH_PWD`

> [!CAUTION]
> Make sure the authentication details in `.env.test` match the ones in `.env`.

```bash
docker compose up -d
poetry run pytest --envfile .env.test tests/
```

If the tests pass, your development environment is ready.

## 4. Create a working branch

> [!NOTE]
> This project follows [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Commit messages help generate the changelog and determine release versions.

Before you make changes, create a **feature branch** with a name that describes what you plan to implement or fix:

```bash
git checkout -b feature/your-feature-name
```

## Next steps

- Updating the docs? The [documentation guide](./documentation-guide.md) has helpful tips.
- Ready to share your work? Open a pull request on GitHub and tell us what changed.
