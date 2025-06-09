# My Chat App

This FastAPI application exposes a small chat API backed by a PostgreSQL database. The app uses OpenAI's API for language generation.

## Environment variables

Create a `.env` file or set the following variables in your environment:

- `DATABASE_URL` – connection string for your PostgreSQL database (for example: `postgresql://user:password@host:5432/dbname`).
- `OPENAI_API_KEY` – your OpenAI API key.

Both variables are required for the app to start.

## Installation

Install the dependencies using `pip`:

```bash
pip install -r requirements.txt
```

## Initialize the database

Create the database tables once before running the API:

```bash
python create_tables.py
```

This uses `DATABASE_URL` to connect and create all tables defined in `models`.

## Running the server

Start the FastAPI server with uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available on `http://localhost:8000` by default.

## API endpoints (summary)

| Method & Path                       | Description                                |
| ---------------------------------- | ------------------------------------------ |
| `GET /`                            | Health check returning a simple message.   |
| `GET /reset-db`                    | Drop and recreate all tables.              |
| `POST /users/`                     | Create a new user.                         |
| `POST /characters/`                | Create a character.                        |
| `PUT /characters/{name}`           | Update character details by name.          |
| `GET /characters/`                 | List all characters.                       |
| `DELETE /characters/{id}`          | Delete a character by ID.                  |
| `POST /chat`                       | Send a message and receive a reply. Use `include_prompt=true` to also return the OpenAI prompt.        |
| `POST /history/`                   | Store a chat message manually.             |
| `GET /history/{user_id}/{character_id}` | Retrieve recent chat history.         |
| `POST /evaluate-liking`            | Update the character's liking score.       |
| `POST /constructs/`                | Create one or multiple value axis constructs. |
| `GET /constructs/{user_id}/{character_id}` | List constructs for a user and character. |
| `DELETE /constructs/{id}`          | Delete a construct by ID. |
| `POST /constructs/import`          | Import constructs from JSONL. |
| `GET /constructs/export/{user_id}/{character_id}` | Export constructs as JSONL. |

See the `schemas` module for request and response shapes for each endpoint.

