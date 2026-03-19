# GridMind — System Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  UNRAID SERVER (192.168.1.2)                                        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FRONTEND CONTAINER (Nginx + React)  :3000                   │  │
│  │                                                              │  │
│  │  Pages:                                                      │  │
│  │  • Dashboard    — live battery/solar/price/immersion status  │  │
│  │  • Prices       — 48hr forecast chart with action overlay    │  │
│  │  • Immersions   — device registry, rules, schedules, targets │  │
│  │  • History      — SOC/solar/price/temperature charts         │  │
│  │  • Controls     — manual overrides, force charge/discharge   │  │
│  │  • Settings     — all config editable in UI                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                    ↕ REST API + WebSocket (/ws)                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  BACKEND CONTAINER (Python FastAPI)  :8000                   │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  APScheduler (replaces Node-RED automation)          │    │  │
│  │  │  • Every 5min:  optimize → apply to HA              │    │  │
│  │  │  • Every 30min: refresh Octopus prices              │    │  │
│  │  │  • Every 1min:  evaluate immersion rules + temp     │    │  │
│  │  │  • On change:   push state via WebSocket            │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  LP Optimizer (core/optimizer.py)                    │    │  │
│  │  │  • 24-48hr price lookahead                          │    │  │
│  │  │  • Configurable constant load assumption             │    │  │
│  │  │  • Fixed SEG export price (configurable)            │    │  │
│  │  │  • Battery charge/discharge scheduling              │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  Configurable Rules Engine (core/rules_engine.py)   │    │  │
│  │  │  • N immersion devices                              │    │  │
│  │  │  • Per-device: smart rules, schedules, temp targets │    │  │
│  │  │  • All thresholds from DB (no hardcoded values)     │    │  │
│  │  │  • AND/OR condition logic per rule                  │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  Action Executor (core/action_executor.py)           │    │  │
│  │  │  • Applies optimizer + rules decisions to HA        │    │  │
│  │  │  • Only calls HA when state actually changes        │    │  │
│  │  │  • Logs every action to system_actions table        │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │  WebSocket Manager (websocket/manager.py)            │    │  │
│  │  │  • Manages all browser connections                  │    │  │
│  │  │  • Broadcasts state updates on change               │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ↕ SQL (SQLAlchemy)                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  MARIADB CONTAINER  :3306  (database: gridmind)              │  │
│  │                                                              │  │
│  │  Existing tables (migrated from battery_optimizer):          │  │
│  │  • electricity_prices                                        │  │
│  │  • optimization_results                                      │  │
│  │  • system_states                                             │  │
│  │  • price_analysis                                            │  │
│  │  • manual_overrides                                          │  │
│  │  • schedule_overrides                                        │  │
│  │                                                              │  │
│  │  New tables:                                 │  │
│  │  • immersion_devices      — device registry                  │  │
│  │  • immersion_smart_rules  — configurable rule engine         │  │
│  │  • temperature_targets    — "ensure X°C by Y time"           │  │
│  │  • system_actions         — audit log of all HA calls        │  │
│  │  • system_settings        — all config (replaces .env)       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ↕ HTTP                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  INFLUXDB CONTAINER  :8086  (bucket: battery-optimizer)      │  │
│  │  • Existing measurements preserved exactly                   │  │
│  │  • New: temperature fields added to system_state             │  │
│  │  • New: immersion_action measurement                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ HTTP REST
┌─────────────────────────────────────────────────────────────────────┐
│  HOME ASSISTANT VM (192.168.1.3:8123)                               │
│                                                                     │
│  Fox Inverter:                                                      │
│  • sensor.foxinverter_battery_soc                                   │
│  • select.foxinverter_work_mode                                     │
│  • number.foxinverter_max_discharge_current                         │
│  • sensor.pv_power_foxinverter                                      │
│  • sensor.solcast_pv_forecast_*                                     │
│                                                                     │
│  Immersion Heaters:                                                 │
│  • switch.immersion_switch                                          │
│  • switch.immersion_lucy_switch                                     │
│  • sensor.sonoff_1001e116e1_temperature                             │
│  • sensor.t_h_sensor_with_external_probe_temperature_2              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: gridmind-backend
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - DB_HOST=mariadb
      - DB_PORT=3306
      - DB_NAME=gridmind
    depends_on:
      mariadb:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./backend:/app  # For development hot-reload

  frontend:
    build: ./frontend
    container_name: gridmind-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  mariadb:
    image: mariadb:10.11
    container_name: gridmind-mariadb
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: gridmind
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mariadb_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  influxdb:
    image: influxdb:2.7
    container_name: gridmind-influxdb
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2
    restart: unless-stopped

volumes:
  mariadb_data:
  influxdb_data:
```

### Minimal .env

```env
# GridMind minimal .env
# All other settings are stored in the database and editable via the UI

# Database (required at startup)
DB_HOST=mariadb
DB_PORT=3306
DB_USER=gridmind
DB_PASSWORD=your_secure_password
DB_ROOT_PASSWORD=your_root_password
DB_NAME=gridmind

# Log level (requires restart to change)
LOG_LEVEL=INFO
```

### Frontend Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Nginx Config

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Proxy API calls to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Proxy WebSocket
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # SPA routing — all other routes serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| GridMind UI | http://192.168.1.2:3000 | Main web interface |
| API | http://192.168.1.2:8000 | REST API |
| API Docs | http://192.168.1.2:8000/docs | Swagger UI |
| InfluxDB | http://192.168.1.2:8086 | Time-series DB |

---

## Migration Path

1. **Keep Node-RED running** during Phase 1-3 development
2. **Phase 1 complete** → Python scheduler takes over automation, disable Node-RED flows
3. **Phase 4-6 complete** → React UI available at :3000
4. **Cutover** → Stop Node-RED, use GridMind exclusively
5. **Archive** → Keep `nodered/` directory as reference, don't delete
