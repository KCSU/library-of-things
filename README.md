# Library of Things

![Version](https://img.shields.io/badge/version-1.1.3-blue)

A web application for lending items to KCSU members.

## Running locally

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- MySQL instance running locally

### 1. Install dependencies

```sh
uv sync
```

### 2. Configure the environment

Copy the example file and fill it in:

```sh
cp .env.example .env
```

### 3. Start the app

```sh
uv run python -m app.run
```

## Development

```sh
uv run ruff check    # lint
uv run ruff format   # format
uv run ty check      # type check
```
