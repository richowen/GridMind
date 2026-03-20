# GridMind — Unraid Deployment

GridMind uses your **existing** MariaDB and InfluxDB instances on Unraid. No bundled databases — just the two GridMind containers managed via the Unraid Docker GUI.

---

## Prerequisites

Before deploying, ensure you have:

1. **MariaDB** running on Unraid at `192.168.1.2:3306`
   - Create a database and user for GridMind. Choose a password and use it in **both** the SQL below and the container's `DB_PASSWORD` variable — they must match:
     ```sql
     -- Replace 'your_secure_password' with the value you will set in DB_PASSWORD
     CREATE DATABASE gridmind CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     CREATE USER 'gridmind'@'%' IDENTIFIED BY 'your_secure_password';
     GRANT ALL PRIVILEGES ON gridmind.* TO 'gridmind'@'%';
     FLUSH PRIVILEGES;
     ```

2. **InfluxDB 2.x** running on Unraid at `192.168.1.64` (on `br0`)
   - Have your InfluxDB **URL**, **token**, **org**, and **bucket** ready — you'll enter these in the GridMind Settings UI after first launch.

3. **Two free IPs** on your `192.168.1.0/24` subnet, outside your DHCP range:
   - `192.168.1.75` — GridMind backend
   - `192.168.1.76` — GridMind frontend

> **Why macvlan/br0?** InfluxDB is on the `br0` macvlan network and blocks requests from outside the `192.168.1.0/24` subnet. Placing GridMind containers on the same network ensures they can reach InfluxDB.

---

## Deployment — Individual Container Templates

Manage each container separately via the Unraid Docker UI using the provided XML templates.

> **Important:** Both containers must be on the `br0` network with their static IPs. The frontend nginx proxy resolves the backend by hostname `backend` — this works because the `--add-host=backend:192.168.1.75` flag is set in the template's ExtraParams.

### Template files

| File                      | Container              | Image                                       |
|---------------------------|------------------------|---------------------------------------------|
| `gridmind-backend.xml`    | gridmind-backend       | `ghcr.io/richowen/gridmind-backend:latest`  |
| `gridmind-frontend.xml`   | gridmind-frontend      | `ghcr.io/richowen/gridmind-frontend:latest` |

### Installation

1. In Unraid → **Docker** → **Add Container**, click **Template repositories** and add:
   ```
   https://raw.githubusercontent.com/richowen/GridMind/main/unraid/
   ```
   Or manually import each XML file.

2. Copy `unraid/nginx.conf` from the repo to `/mnt/user/appdata/gridmind/nginx.conf`.

3. Start **gridmind-backend** first — set `DB_HOST` to `192.168.1.2` and fill in `DB_PASSWORD` (same password as the `CREATE USER` SQL above). Then start **gridmind-frontend**.

4. Both containers will be assigned their static IPs on `br0` automatically from the template defaults.

### Access

| Service  | Address                          | Purpose                  |
|----------|----------------------------------|--------------------------|
| Frontend | `http://192.168.1.76:3009`       | Web dashboard            |
| Backend  | `http://192.168.1.75:8009`       | API + WebSocket          |
| API Docs | `http://192.168.1.75:8009/docs`  | FastAPI Swagger UI       |

---

## Updating

Use Unraid's **Check for Updates** button on each container to pull the latest `ghcr.io` images and restart.

---

## Networking notes

Both containers are placed on Unraid's `br0` macvlan network with static IPs. The static IPs (`192.168.1.75` and `192.168.1.76`) must be outside your router's DHCP range to avoid conflicts.

The frontend nginx config (mounted from `/mnt/user/appdata/gridmind/nginx.conf`) proxies all `/api/` and `/ws` traffic to the backend at `backend:8009`, resolved via the `--add-host` flag in the frontend template.
