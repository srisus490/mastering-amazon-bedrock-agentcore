# Docker Setup for File Monitoring System

This directory contains Docker configuration files for local development of the Intelligent Source Files Monitoring System.

## Services

The Docker Compose setup includes the following services:

1. **PostgreSQL** (port 5432) - Relational database for configuration and metadata
2. **InfluxDB** (port 8086) - Time-series database for file arrival timestamps
3. **Redis** (port 6379) - Cache layer for dashboard and real-time data
4. **RabbitMQ** (ports 5672, 15672) - Message queue for event processing

## Quick Start

### 1. Start all services

```bash
docker-compose up -d
```

### 2. Check service health

```bash
docker-compose ps
```

All services should show "healthy" status after a few seconds.

### 3. Access service UIs

- **RabbitMQ Management**: http://localhost:15672
  - Username: `monitoring_user`
  - Password: `rabbitmq_pass`

- **InfluxDB UI**: http://localhost:8086
  - Username: `admin`
  - Password: `adminpass123`

### 4. Stop all services

```bash
docker-compose down
```

### 5. Stop and remove all data

```bash
docker-compose down -v
```

## Service Details

### PostgreSQL

- **Database**: `file_monitoring`
- **User**: `monitoring_user`
- **Password**: `monitoring_pass`
- **Connection String**: `postgresql://monitoring_user:monitoring_pass@localhost:5432/file_monitoring`

The database schema is automatically initialized on first startup using the script in `init-scripts/postgres/01-init-schema.sql`.

### InfluxDB

- **Organization**: `file_monitoring_org`
- **Bucket**: `file_arrivals`
- **Token**: `monitoring-token-secret-key`
- **Retention**: 90 days for raw data

### Redis

- **Password**: `redis_pass`
- **Connection**: `redis://:redis_pass@localhost:6379/0`

### RabbitMQ

- **Virtual Host**: `/`
- **Queue**: `file-arrivals`
- **Exchange**: `file-events` (topic)
- **Dead Letter Queue**: `file-arrivals-dlq`

## Troubleshooting

### Check logs for a specific service

```bash
docker-compose logs -f postgres
docker-compose logs -f influxdb
docker-compose logs -f redis
docker-compose logs -f rabbitmq
```

### Restart a specific service

```bash
docker-compose restart postgres
```

### Connect to PostgreSQL

```bash
docker exec -it monitoring-postgres psql -U monitoring_user -d file_monitoring
```

### Connect to Redis CLI

```bash
docker exec -it monitoring-redis redis-cli -a redis_pass
```

### Reset everything

```bash
docker-compose down -v
docker-compose up -d
```

## Data Persistence

All service data is persisted in Docker volumes:

- `postgres_data` - PostgreSQL data
- `influxdb_data` - InfluxDB data
- `influxdb_config` - InfluxDB configuration
- `redis_data` - Redis data
- `rabbitmq_data` - RabbitMQ data

To view volumes:

```bash
docker volume ls | grep monitoring
```

## Network

All services are connected via the `monitoring-network` bridge network, allowing them to communicate with each other using service names as hostnames.
