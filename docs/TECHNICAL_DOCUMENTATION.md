# Intelligent File Monitoring System
## Technical Documentation

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Client)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  index.html  │  │  CSS Themes  │  │  JavaScript Modules  │  │
│  │  (SPA shell) │  │  main.css    │  │  app.js              │  │
│  │              │  │  themes.css  │  │  ui-manager.js       │  │
│  │              │  │  chat.css    │  │  api-client.js       │  │
│  │              │  │              │  │  state-manager.js    │  │
│  │              │  │              │  │  chart-renderer.js   │  │
│  │              │  │              │  │  ai-insights-manager │  │
│  │              │  │              │  │  chat-widget.js      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST (localhost:8000)
┌────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend (Python)                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Routes                            │    │
│  │  /api/v1/file-arrivals    /api/v1/sla/                  │    │
│  │  /api/v1/trends/          /api/v1/ai/                   │    │
│  │  /api/v1/chat/                                          │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                    │
│  ┌──────────────┐  ┌────────▼───────┐  ┌────────────────────┐  │
│  │  SLA Module  │  │  Analytics     │  │  AI Module         │  │
│  │  calculator  │  │  trend_analyzer│  │  cohere_client.py  │  │
│  │  tracker     │  │  pattern_detect│  │  insights_engine   │  │
│  └──────┬───────┘  └────────┬───────┘  └────────┬───────────┘  │
│         │                   │                    │              │
│  ┌──────▼───────────────────▼────────────────────▼───────────┐  │
│  │              SQLite Database (file_monitoring.db)          │  │
│  │  file_arrivals  │  sla_violations  │  sla_scores          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Cohere API     │
                    │  Command R+     │
                    │  (cloud)        │
                    └─────────────────┘
```

---

## 2. Project Structure

```
mastering-amazon-bedrock-agentcore/
├── run_api.py                    # API server entry point
├── .env                          # Environment variables (COHERE_API_KEY)
├── alembic/                      # Database migrations
│   └── env.py
├── src/
│   ├── api/
│   │   ├── main.py               # FastAPI app factory
│   │   └── routes/
│   │       ├── file_arrivals.py  # File arrival endpoints
│   │       ├── sla.py            # SLA score & violation endpoints
│   │       ├── trends.py         # Trend analysis endpoints
│   │       ├── ai.py             # AI insights endpoints
│   │       └── chat.py           # Chat/agent endpoint
│   ├── ai/
│   │   ├── cohere_client.py      # Cohere API wrapper
│   │   ├── config.py             # AI configuration
│   │   ├── insights_engine.py    # Smart insights generator
│   │   ├── forecast_engine.py    # 7-day forecast generator
│   │   ├── root_cause_analyzer.py# Root cause analysis
│   │   └── intelligent_query_parser.py # NL query parser
│   ├── analytics/
│   │   └── trend_analyzer.py     # Daily/hourly trend calculations
│   ├── sla/
│   │   ├── calculator.py         # SLA score calculation
│   │   └── tracker.py            # Violation recording & querying
│   ├── database/
│   │   ├── connection.py         # SQLite session management
│   │   └── models.py             # SQLAlchemy ORM models
│   └── core/
│       ├── config.py             # App settings (pydantic)
│       └── logging.py            # Structured logging
├── web-dashboard/
│   ├── index.html                # Single page application shell
│   ├── config/
│   │   └── config.json           # Frontend configuration
│   ├── css/
│   │   ├── main.css              # Core styles + dark mode
│   │   ├── themes.css            # CSS variables for themes
│   │   └── chat.css              # Chat panel styles
│   └── js/
│       ├── app.js                # Application orchestrator
│       ├── api-client.js         # HTTP client with caching & retry
│       ├── state-manager.js      # Centralised state (observer pattern)
│       ├── ui-manager.js         # DOM rendering & event handling
│       ├── chart-renderer.js     # Chart.js wrappers
│       ├── ai-insights-manager.js# AI panel rendering
│       ├── chat-widget.js        # Chat UI component
│       ├── chat-manager.js       # Chat session management
│       ├── message-formatter.js  # Message rendering
│       ├── theme-manager.js      # Light/dark mode toggle
│       └── date-presets.js       # Quick date range buttons
└── docs/
    ├── VP_PRESENTATION.md
    ├── SLA_REFERENCE.md
    └── TECHNICAL_DOCUMENTATION.md
```

---

## 3. Database Schema

### `file_arrivals`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| filename | TEXT | File name |
| source_system_id | TEXT | Source system identifier |
| arrival_timestamp | DATETIME | When file arrived |
| file_size_bytes | INTEGER | File size |
| checksum | TEXT | MD5/SHA checksum |
| status | TEXT | processed / pending / failed |

### `sla_violations`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| source_system_id | TEXT | Source system |
| violation_date | DATE | Date of violation |
| violation_type | TEXT | Type (e.g. MISSED_FILE, LATE_ARRIVAL) |
| expected_value | TEXT | What was expected |
| actual_value | TEXT | What actually happened |
| severity | TEXT | critical / high / medium / low |
| created_at | DATETIME | Record creation time |

### `sla_scores`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| source_system_id | TEXT | Source system |
| score_date | DATE | Date of score |
| score | FLOAT | Score value 0–100 |
| total_checks | INTEGER | Total checks performed |
| passed_checks | INTEGER | Checks that passed |
| calculated_at | DATETIME | When score was calculated |

---

## 4. API Endpoints

### File Arrivals
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/file-arrivals` | List arrivals with filters |
| GET | `/api/v1/file-arrivals/count` | Count arrivals |

### SLA
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sla/scores/{system_id}` | Daily scores for system |
| GET | `/api/v1/sla/average-score/{system_id}` | Average score over period |
| GET | `/api/v1/sla/violations` | List violations with filters |
| GET | `/api/v1/sla/violations/by-severity/{system_id}` | Violation counts by severity |

### Trends
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/trends/daily/{system_id}` | Daily file count trend |
| GET | `/api/v1/trends/moving-average/{system_id}` | 7-day moving average |
| GET | `/api/v1/trends/hourly-patterns/{system_id}` | Hourly arrival patterns |
| GET | `/api/v1/trends/summary` | All systems summary |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/insights` | Smart insights for system |
| POST | `/api/v1/ai/forecast` | 7-day forecast |
| POST | `/api/v1/ai/root-cause` | Root cause analysis |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/agent` | Natural language query |
| GET | `/api/v1/chat/examples` | Example questions |
| POST | `/api/v1/chat/clear` | Clear session cache |

---

## 5. Frontend Architecture

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `app.js` | Orchestrates lifecycle, wires events, calls refresh methods |
| `state-manager.js` | Single source of truth; observer pattern for state changes |
| `ui-manager.js` | All DOM rendering; no business logic |
| `api-client.js` | HTTP calls with 30s cache, 3-retry exponential backoff |
| `chart-renderer.js` | Chart.js chart creation and destruction |
| `ai-insights-manager.js` | Fetches and renders AI panel content |
| `chat-widget.js` | Chat drawer UI, message display |
| `chat-manager.js` | Session management, API calls for chat |

### State Flow
```
User Action
    │
    ▼
StateManager.set*()  ──► notify(eventType)
                              │
                    ┌─────────▼──────────┐
                    │  app.js subscribers │
                    │  handleFilterChange │
                    │  handleSystemSelect │
                    │  handleDateRange    │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  refreshOverview() │
                    │  refreshSystem()   │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  APIClient.get*()  │
                    │  (cached 30s)      │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  UIManager.render* │
                    │  (DOM update)      │
                    └────────────────────┘
```

---

## 6. SLA Score Calculation (Detail)

```python
# Per day:
score = 100.0 - (len(violations_on_day) * 10.0)
score = max(0.0, score)

# Average over period:
avg = sum(daily_scores) / len(daily_scores)
```

Scores are cached in `sla_scores` table. On first request for a date, the score is calculated and stored. Subsequent requests use the cached value.

---

## 7. AI Integration

### Cohere Command R+ (command-r-plus-08-2024)

The chat endpoint (`/api/v1/chat/agent`) works as follows:

1. Parse the user query with `IntelligentQueryParser` to detect system names (case-insensitive)
2. If a system is mentioned, fetch last 14 days of trend data from DB
3. Format the data as a human-readable context string
4. Send to Cohere with a system prompt instructing concise (2–4 sentence) responses
5. Return the response to the frontend

The AI insights endpoints use the same Cohere client but with structured prompts for trend analysis, forecasting, and root cause analysis.

### Environment Variable
```
COHERE_API_KEY=your_key_here   # in .env file
```

---

## 8. Running the System

### Prerequisites
```bash
python 3.11+
pip install -e ".[dev]"
```

### Start API Server
```bash
python run_api.py
# Runs on http://localhost:8000
```

### Start Dashboard
```bash
python -m http.server 3000 --directory web-dashboard
# Open http://localhost:3000
```

### Populate Test Data
```bash
python simulate_file_transfers.py   # Add file arrival records
python simulate_sla_violations.py   # Add SLA violation records
```

---

## 9. Configuration

### `web-dashboard/config/config.json`
```json
{
  "apiBaseURL": "http://localhost:8000",
  "refreshInterval": 30000,
  "cacheTimeout": 30000,
  "retryAttempts": 3,
  "retryBackoff": 100,
  "paginationPageSize": 30
}
```

### `.env`
```
COHERE_API_KEY=your_cohere_api_key
DATABASE_URL=sqlite:///./data/file_monitoring.db
```

---

## 10. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite over PostgreSQL | Zero infrastructure, portable, sufficient for current scale |
| Vanilla JS over React | No build step, instant load, easier to maintain |
| Observer pattern in StateManager | Decouples UI from data; single source of truth |
| 30s API cache in APIClient | Reduces backend load during auto-refresh |
| Cohere over AWS Bedrock | Direct API, no AWS credentials required, simpler setup |
| Version query strings on JS imports | Forces cache bust on deployment without server config |

---

*Technical Documentation — March 2026*
