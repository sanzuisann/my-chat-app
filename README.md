# My Chat App

This repository contains a small chat application split into two parts:

* **backend/** – a FastAPI service backed by PostgreSQL and OpenAI.
* **unity-client/** – a Unity project that talks to the API.

## Backend

### Environment variables
Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```
DATABASE_URL=<postgres connection url>
OPENAI_API_KEY=<your OpenAI key>
```

### Installation

Install the Python requirements:

```bash
pip install -r requirements.txt
```

### Initialize the database

Run once to create all tables:

```bash
python -m backend.create_tables
```

### Creating characters

Add at least one character so the client has something to talk to. Characters
are created by POSTing JSON to `/characters/`:

```bash
curl -X POST http://localhost:8000/characters/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Alice", "personality": "calm", "system_prompt": "You are Alice."}'
```

Existing characters and their IDs can be listed via:

```bash
curl http://localhost:8000/characters/
```

These `id` fields are UUIDs. Unity scripts such as `ChatManager`,
`TrustEvaluator` and others reference them through their `characterId` fields, so
update the values in your Unity scene after creating characters.

### Running the API server

Start the server from the repository root:

```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000` by default.

## Unity client

Open the `unity-client/` folder with Unity Hub or the Unity editor. The C# scripts
are stored in `Assets/Scripts/`.

The API base URL is controlled by `ApiConfig.cs`. By default it uses
`http://localhost:8000`, but you can override this by setting the PlayerPrefs
key `API_BASE_URL` (or an environment variable of the same name) before
running the client.

Build or run the scene from the editor to debug the client.

## Layout

```
backend/            FastAPI application
  main.py           API entry point
  create_tables.py  Utility to create tables
  crud/             Database operations
  db/               SQLAlchemy setup
  dependencies/     Dependency helpers
  models/           ORM models
  schemas/          Pydantic schemas
  data/             Optional JSON data files
unity-client/       Unity project
  Assets/
    Scripts/        Client scripts
```
