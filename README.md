# My Chat App

This repository contains a small chat application split into two parts:

* **backend/** – a FastAPI service backed by PostgreSQL and OpenAI.
* **unity-client/** – a Unity project that talks to the API.

## Backend

### Environment variables
Create a `.env` file with at least the following entries:

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

### Running the API server

Start the server from the repository root:

```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000` by default.

## Unity client

Open the `unity-client/` folder with Unity Hub or the Unity editor. The C# scripts
are stored in `Assets/Scripts/`. If you need to use a different API endpoint,
edit the URL value in the networking script (for example `ChatManager.cs`).

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
