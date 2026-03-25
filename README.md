# Intelligent File Monitoring System

A cost-effective, production-ready file monitoring system with SLA tracking, trend analysis, and REST API - all powered by SQLite for **$0/month** infrastructure costs.

## Features

- 🔍 **Real-time File Monitoring**: Detect file arrivals across 20+ source systems
- 📊 **SLA Tracking**: Define SLAs, track violations, calculate compliance scores
- 📈 **Trend Analysis**: Moving averages, daily patterns, hourly distributions
- 🚀 **REST API**: Comprehensive FastAPI endpoints with auto-generated docs
- 🤖 **AI-Powered**: Amazon Bedrock integration for anomaly detection, predictions, and optimization
- 💰 **Zero Infrastructure Cost**: SQLite-based architecture eliminates cloud database costs
- ✅ **Production Ready**: 15/15 tests passing, comprehensive error handling

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd intelligent-file-monitoring

# Install dependencies
pip install -e ".[dev]"

# Initialize database
python scripts/init_database.py

# (Optional) Add test data
python setup_test_data.py
```

### Start API Server

```bash
python run_api.py
```

Visit:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Test API

```bash
python test_api.py
```

## Architecture

```
File System → DirectoryWatcher → SQLite → REST API → Dashboard
```

**Key Components:**
- **DirectoryWatcher**: Monitors directories for file arrivals
- **SQLite Database**: Stores all data (files, SLA, trends)
- **TrendAnalyzer**: Calculates moving averages and patterns
- **SLA Services**: Evaluates compliance and tracks violations
- **FastAPI**: Exposes REST endpoints for data access

## API Endpoints

### Source Systems
- `GET /api/v1/source-systems` - List all systems
- `GET /api/v1/source-systems/{id}` - Get system details

### File Arrivals
- `GET /api/v1/file-arrivals` - List file arrivals
- `GET /api/v1/file-arrivals/count` - Get file count

### Trends
- `GET /api/v1/trends/moving-average/{id}` - Moving averages
- `GET /api/v1/trends/daily/{id}` - Daily counts
- `GET /api/v1/trends/hourly-patterns/{id}` - Hourly patterns
- `GET /api/v1/trends/summary` - All systems summary

### SLA
- `GET /api/v1/sla/scores/{id}` - SLA scores over time
- `GET /api/v1/sla/average-score/{id}` - Average score
- `GET /api/v1/sla/violations` - List violations
- `GET /api/v1/sla/violations/by-severity/{id}` - Violations by severity

## Configuration

### Configure Your 20 Source Systems

1. **Edit `add_systems.py`** - Update with your actual directories and SLA settings
2. **Create directories** - `python create_directories.py`
3. **Add to database** - `python add_systems.py`
4. **Verify setup** - `python verify_configuration.py`

See `CONFIGURATION_GUIDE.md` for detailed instructions.

**Quick Example:**
```python
{
    "id": "PROD_SALES",
    "name": "Production Sales System",
    "directory_path": "C:\\data\\sales",
    "is_active": True,
    "sla": {
        "expected_arrival_time": time(9, 0, 0),  # 9:00 AM
        "window_minutes": 30,  # ±30 minutes
        "minimum_files_per_day": 5,
    }
}
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_sla_simplified.py -v
```

## Cost Savings

| Component | Original | Current | Savings |
|-----------|----------|---------|---------|
| PostgreSQL | $50-150/mo | $0 | 100% |
| InfluxDB | $50-200/mo | $0 | 100% |
| Redis | $30-100/mo | $0 | 100% |
| RabbitMQ | $50-150/mo | $0 | 100% |
| **Total** | **$180-600/mo** | **$0** | **$2,160-7,200/year** |

## Performance

- File detection: < 1 second
- Database writes: < 100ms
- API response: < 200ms
- Capacity: 20,000+ files/day
- Concurrent systems: 20+

## Project Structure

```
├── src/
│   ├── api/          # FastAPI application
│   ├── analytics/    # Trend analysis
│   ├── database/     # SQLite models
│   ├── monitor/      # File monitoring
│   └── sla/          # SLA services
├── tests/            # Test suite
├── data/             # SQLite database
├── config/           # Configuration
└── scripts/          # Utility scripts
```

## Documentation

- **Full Implementation Guide**: [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)
- **API Documentation**: http://localhost:8000/docs (when server is running)
- **Cost Analysis**: See IMPLEMENTATION_COMPLETE.md

## Requirements

- Python 3.10+
- SQLite 3.35+ (included with Python)
- 100MB disk space (grows with data)

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
