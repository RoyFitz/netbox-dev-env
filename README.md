# NetBox Dev Environment

A portable NetBox development environment with pre-configured test data.

## Prerequisites

- Docker Desktop installed and running
- Git (to clone this repo)

## Quick Start

1. **Clone this repository**
   ```
   git clone <repo-url>
   cd netbox-dev-env
   ```

2. **Start NetBox**
   ```
   docker compose up -d
   ```

3. **Wait for startup** (first time takes 2-3 minutes to pull images and initialize)
   ```
   docker compose logs -f netbox
   ```
   Wait until you see `Listening at: http://0.0.0.0:8080`

4. **Import the test data**
   ```
   docker compose exec netbox python /scripts/import_data.py
   ```

5. **Open NetBox**
   - URL: http://localhost:8000
   - Username: `admin`
   - Password: `admin`

## Commands

| Action | Command |
|--------|---------|
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| View logs | `docker compose logs -f netbox` |
| Import data | `docker compose exec netbox python /scripts/import_data.py` |
| Reset everything | `docker compose down -v` (deletes all data) |

## Adding/Modifying Data

Edit the YAML files in the `data/` folder, then re-run the import command.

The import script will skip objects that already exist, so it's safe to run multiple times.

## Troubleshooting

**NetBox won't start:**
- Make sure Docker Desktop is running
- Check logs: `docker compose logs netbox`
- Try resetting: `docker compose down -v && docker compose up -d`

**Import fails:**
- Make sure NetBox is fully started (check logs for "Listening at...")
- Check your YAML syntax

**Port 8000 already in use:**
- Edit `docker-compose.yml` and change `8000:8080` to another port like `8080:8080`
