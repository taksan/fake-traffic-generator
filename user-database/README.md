# User Database Service

A simple Flask-based user database service that manages up to 100 users and logs all requests.

## Features

- **User Management**: Stores up to 100 users with ID and name
- **Random User API**: Returns either an existing user or creates a new one (up to limit)
- **Request Logging**: Logs every request in JSON format for ingestion into ELK
- **Persistent Storage**: Uses JSON file storage with Docker volume

## Port

The service runs on port **8500**.

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

### `GET /user/random`
Get a random user. Returns an existing user (70% chance) or creates a new one (30% chance, if under 100 limit).

**Response (existing user):**
```json
{
  "id": 42,
  "name": "John Doe"
}
```

**Response (new user - 201 Created):**
```json
{
  "id": 1,
  "name": "Jane Smith"
}
```

### `GET /users`
Get all users with count information.

**Response:**
```json
{
  "count": 42,
  "max": 100,
  "users": [
    {"id": 1, "name": "John Doe"},
    {"id": 2, "name": "Jane Smith"}
  ]
}
```

### `POST /users/reset`
Reset all users (for testing purposes).

**Response:**
```json
{
  "message": "Users reset successfully"
}
```

## Log Format

Each request generates a log entry in JSON format:

```json
{
  "timestamp": "2025-10-15T22:15:59.123456Z",
  "service": "user-database",
  "action": "created_new",
  "user_id": 1,
  "user_name": "John Doe"
}
```

### Log Actions
- `created_new`: A new user was created
- `returned_existing`: An existing user was returned
- `returned_existing_max_reached`: Max users reached, returned existing user

## Integration

The user database integrates with the traffic generator:
1. Log generator calls `/user/random` to get users
2. User database logs each request to `/data/user_database.log`
3. Filebeat collects logs and sends to Logstash
4. Logstash routes to `user-database-logs-*` index in Elasticsearch
5. Kibana displays logs in a separate data view

## Data Persistence

- **Users**: `/data/users.json`
- **Logs**: `/data/user_database.log`

Both are persisted in the `user_data` Docker volume.
