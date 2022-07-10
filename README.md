# Chan backend
Periodically scrapes the chan and provides a REST API to access its contents.

## Getting Started

### Prerequisites
- [database](https://github.com/how2die/database)
- [keycloak](https://github.com/how2die/keycloak)

### Create database schemas
1. Create a database named `chan`
2. Import table structures from `persistence/init.sql`

### Configure permissions
1. Create Keycloak client `chan` with Access Type `bearer-only`
2. Create realm role `chan` and bind to relevant users.

### Run with python
From the `src` folder run: `python -m uvicorn main:app --reload`

### Run in Docker
Running with Docker example: `docker run -e DB_HOST=db -e DB_PORT=5432 -e DB_NAME=chan -e AUTH_HOST=http://auth:8080 -e FLASK_DEBUG=1 --name chan-backend --link some-postgres:db --link keycloak:auth -p 8000:8000 how2die/chan-backend`

### Configuration
Configuration is done using environment variables in accordance with the [12-factor app](https://12factor.net/). If not specified, the variable will default to the value shown in parantheses.

- `DL_FOLDER`: path to download folder. (`/var/chan/downloads/`)
- `FAVS_FOLDER`: path to favorites folder. (`/var/chan/favorites/`)
- `DB_HOST`: database host. (`localhost`)
- `DB_PORT`: database port. (`5432`)
- `DB_NAME`: database name. (`chan`)
- `DB_USER`: database username. (`postgres`)
- `DB_PASSWORD`: database password. (`postgres`)
- `AUTH_HOST`: authentication server host uri. (`http://localhost:1234`)

## Usage
Usage of the REST API is documented by the OpenAPI specification located at `localhost:8000/openapi.json`.

## Development
For local development environment variables may be defined in a `.env` file in the root folder. 

To build the Docker project, run `docker build -t how2die/chan-backend .`
