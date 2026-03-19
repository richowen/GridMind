# GridMind — Unraid Deployment

GridMind uses your **existing** MariaDB and InfluxDB instances on Unraid. No bundled databases — just the two GridMind containers.

---

## Prerequisites

Before deploying, ensure you have:

1. **MariaDB** running on Unraid at `192.168.1.2:3306`
   - Create a database and user for GridMind. Choose a password and use it in **both** the SQL below and your `.env` file — they must match:
     ```sql
     -- Replace 'your_secure_password' with the same value you will put in DB_PASSWORD in your .env
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

## Option A — Compose Manager (Recommended)

Uses the [Compose Manager](https://forums.unraid.net/topic/114415-plugin-docker-compose-manager/) Unraid plugin.

### Steps

1. Install the **Compose Manager** plugin from Unraid Community Applications.

2. Create the appdata directory and copy the required files:
   ```bash
   mkdir -p /mnt/user/appdata/gridmind
   cp /path/to/GridMind/.env.example /mnt/user/appdata/gridmind/.env
   cp /path/to/GridMind/unraid/nginx.conf /mnt/user/appdata/gridmind/nginx.conf
   ```

3. Edit `/mnt/user/appdata/gridmind/.env` — set `DB_PASSWORD` to the **same password** you used in the `CREATE USER` SQL above:
   ```env
   DB_HOST=192.168.1.2
   DB_PORT=3306
   DB_USER=gridmind
   DB_PASSWORD=your_secure_password   # ← must match the SQL password exactly
   DB_NAME=gridmind
   ```

4. Copy `unraid/docker-compose.yml` to `/mnt/user/appdata/gridmind/docker-compose.yml`.

5. In Unraid → **Docker** → **Compose Manager**, click **Add New Stack**, point it at `/mnt/user/appdata/gridmind/docker-compose.yml`, and start it.

6. Open the GridMind UI at `http://192.168.1.76:3009` and configure Home Assistant, Octopus Energy, and InfluxDB settings via the **Settings** page.

### Access

| Service  | Address                          | Purpose                  |
|----------|----------------------------------|--------------------------|
| Frontend | `http://192.168.1.76:3009`       | Web dashboard            |
| Backend  | `http://192.168.1.75:8009`       | API + WebSocket          |
| API Docs | `http://192.168.1.75:8009/docs`  | FastAPI Swagger UI       |

---

## Option B — Individual Container Templates (CA)

Use the XML templates to manage each container separately via the Unraid Docker UI.

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

3. Start **gridmind-backend** first — set `DB_HOST` to `192.168.1.2` and fill in `DB_PASSWORD` (same password as the `CREATE USER` SQL). Then start **gridmind-frontend**.

4. Both containers will be assigned their static IPs on `br0` automatically from the template defaults.

---

## Updating

With Compose Manager, click **Pull** then **Up** to pull the latest `ghcr.io` images and restart.

With individual templates, use Unraid's **Check for Updates** button on each container.

---

## Networking notes

The `br0` macvlan network is defined in the compose file as:

```yaml
networks:
  br0:
    driver: macvlan
    driver_opts:
      parent: br0
    ipam:
      config:
        - subnet: 192.168.1.0/24
          gateway: 192.168.1.1
```

If your gateway is different from `192.168.1.1`, edit the compose file before deploying.

> **Unraid host ↔ macvlan containers:** By default, the Unraid host cannot communicate directly with macvlan containers. This is a Linux kernel limitation. If you need the Unraid host to reach GridMind, create a macvlan shim interface — see the [Unraid forums](https://forums.unraid.net) for guidance. Accessing GridMind from other LAN devices (PC, phone, etc.) works without any extra steps.
