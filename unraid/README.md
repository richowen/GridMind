# GridMind — Unraid Deployment

Two deployment options are available. **Option A (Compose Manager) is recommended** as it handles networking automatically.

---

## Option A — Compose Manager (Recommended)

Uses the [Compose Manager](https://forums.unraid.net/topic/114415-plugin-docker-compose-manager/) Unraid plugin to run the full stack as a single unit.

### Steps

1. Install the **Compose Manager** plugin from Unraid Community Applications.

2. Create the appdata directory and copy the env file:
   ```bash
   mkdir -p /mnt/user/appdata/gridmind
   cp /path/to/GridMind/.env.example /mnt/user/appdata/gridmind/.env
   ```

3. Edit `/mnt/user/appdata/gridmind/.env` and set:
   ```env
   DB_PASSWORD=your_secure_password
   DB_ROOT_PASSWORD=your_root_password
   ```

4. Copy `unraid/docker-compose.yml` to `/mnt/user/appdata/gridmind/docker-compose.yml`.

5. In Unraid → **Docker** → **Compose Manager**, click **Add New Stack**, point it at `/mnt/user/appdata/gridmind/docker-compose.yml`, and start it.

6. Open the GridMind UI at `http://<unraid-ip>:3009` and configure Home Assistant, Octopus Energy, and InfluxDB settings via the **Settings** page.

### Ports

| Service   | Port  | Purpose                        |
|-----------|-------|--------------------------------|
| Frontend  | 3009  | Web dashboard                  |
| Backend   | 8009  | API + WebSocket (internal use) |
| InfluxDB  | 8086  | InfluxDB UI (optional)         |

### Data persistence

All data is stored under `/mnt/user/appdata/gridmind/`:

| Path                                    | Contents              |
|-----------------------------------------|-----------------------|
| `/mnt/user/appdata/gridmind/mariadb`    | MariaDB database      |
| `/mnt/user/appdata/gridmind/influxdb`   | InfluxDB data         |

---

## Option B — Individual Container Templates (CA)

Use the XML templates if you prefer to manage each container separately via the Unraid Docker UI.

> **Important:** The frontend nginx proxy resolves the backend by the hostname `backend`. When running containers individually (not via Compose), you must either:
> - Put both containers on a **custom Docker network** and name the backend container `backend`, **or**
> - Use the Unraid host IP and port 8000 instead (requires rebuilding the frontend image with a different nginx config).
>
> **The Compose Manager approach avoids this complexity entirely.**

### Template files

| File                      | Container              | Image                                      |
|---------------------------|------------------------|--------------------------------------------|
| `gridmind-backend.xml`    | gridmind-backend       | `ghcr.io/richowen/gridmind-backend:latest` |
| `gridmind-frontend.xml`   | gridmind-frontend      | `ghcr.io/richowen/gridmind-frontend:latest`|

### Installation

1. In Unraid → **Docker** → **Add Container**, click **Template repositories** and add:
   ```
   https://raw.githubusercontent.com/richowen/GridMind/main/unraid/
   ```
   Or manually import each XML file.

2. Start **gridmind-backend** first, then **gridmind-frontend**.

3. You will also need a MariaDB container running separately. Set `DB_HOST` in the backend template to the IP/hostname of your MariaDB instance.

---

## Updating

With Compose Manager, click **Pull** then **Up** to pull the latest `ghcr.io` images and restart.

With individual templates, use Unraid's **Check for Updates** button on each container.
