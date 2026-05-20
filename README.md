# NetBox Dev Environment

A ready-to-run NetBox development environment with pre-configured test data.

---

## Before You Start

Make sure you have these installed:
- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download here](https://git-scm.com/downloads)

---

## Step-by-Step Setup

### Step 1: Open Docker Desktop

1. Find **Docker Desktop** in your Start Menu and open it
2. Wait for it to say **"Docker Desktop is running"** (you'll see a green icon in the system tray)
3. Leave Docker Desktop running in the background

### Step 2: Open PowerShell

1. Click the **Start Menu**
2. Type `PowerShell`
3. Click on **Windows PowerShell** (the blue icon)

A blue window will open - this is where you'll type commands.

### Step 3: Go to Your Projects Folder

Type this command and press **Enter**:

```
cd ~\Documents\Github
```

> **What this does:** Navigates to your Github folder in Documents.

### Step 4: Download This Project

Type this command and press **Enter**:

```
git clone https://github.com/RoyFitz/netbox-dev-env.git
```

> **What this does:** Downloads all the project files to your computer.

### Step 5: Enter the Project Folder

Type this command and press **Enter**:

```
cd netbox-dev-env
```

### Step 6: Start NetBox

Type this command and press **Enter**:

```
docker compose up -d
```

> **What this does:** Downloads and starts NetBox and its database. This will take 2-5 minutes the first time.

You'll see text scrolling - that's normal. Wait until you see your cursor again.

### Step 7: Wait for NetBox to Start

Type this command and press **Enter**:

```
docker compose logs -f netbox
```

> **What this does:** Shows you what NetBox is doing while it starts up.

Wait until you see a line that says:
```
Listening at: http://0.0.0.0:8080
```

Once you see that, press **Ctrl + C** to stop watching the logs.

### Step 8: Import the Test Data

Type this command and press **Enter**:

```
docker compose exec netbox python /scripts/import_data.py
```

> **What this does:** Loads the test site, devices, VLANs, and IP addresses into NetBox.

### Step 9: Open NetBox

1. Open your web browser (Chrome, Edge, Firefox)
2. Go to: **http://localhost:8000**
3. Log in with:
   - **Username:** `admin`
   - **Password:** `admin`

---

## You're Done!

You should now see NetBox with the test data loaded.

---

## Common Commands

Open PowerShell and `cd` to the project folder first, then use these commands:

| What You Want To Do | Command |
|---------------------|---------|
| Start NetBox | `docker compose up -d` |
| Stop NetBox | `docker compose down` |
| View logs | `docker compose logs -f netbox` |
| Re-import data | `docker compose exec netbox python /scripts/import_data.py` |
| Delete everything and start fresh | `docker compose down -v` |

---

## Troubleshooting

### "docker: command not found" or similar error
- Make sure Docker Desktop is running (check for the whale icon in your system tray)
- Try closing and reopening PowerShell

### NetBox won't load in browser
- Make sure you waited for the "Listening at..." message in the logs
- Try: `docker compose logs netbox` to see if there are errors

### Import fails with connection error
- Wait a bit longer for NetBox to fully start
- Run `docker compose logs -f netbox` and wait for "Listening at..."

### Need to completely reset everything
Run these commands:
```
docker compose down -v
docker compose up -d
```
Then wait for startup and import data again.

---

## Login Details

| Setting | Value |
|---------|-------|
| URL | http://localhost:8000 |
| Username | admin |
| Password | admin |
| API Token | 0123456789abcdef0123456789abcdef01234567 |
