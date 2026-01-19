# Harpoon - Polymarket Trade Viewer

## Project Overview

A full-stack application that allows users to view all Polymarket trades for a given wallet address or Polymarket profile URL. Shows trade history with exact timestamps and links to Polygonscan for transaction details.

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend | Python + FastAPI | Async support, automatic OpenAPI docs, excellent for data processing |
| Frontend | Next.js 14 | SSR capabilities, React ecosystem, easy Railway deployment |
| Database | PostgreSQL | Structured trade data, Railway native support, reliable |
| Data Sources | Polygon RPC + TheGraph | Direct blockchain access, indexed data via subgraphs |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Next.js UI    │────▶│  FastAPI API    │────▶│   PostgreSQL    │
│   (Frontend)    │     │   (Backend)     │     │   (Cache/DB)    │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
           ┌───────────────┐        ┌───────────────┐
           │  Polygon RPC  │        │   TheGraph    │
           │  (Alchemy)    │        │  (Subgraph)   │
           └───────────────┘        └───────────────┘
```

## Data Flow

1. User enters Polymarket profile URL or Polygon wallet address
2. Frontend sends request to FastAPI backend
3. Backend parses input to extract wallet address
4. Backend queries:
   - TheGraph subgraph for indexed Polymarket trades
   - Polygon RPC for additional transaction details if needed
5. Results cached in PostgreSQL for faster subsequent queries
6. Frontend displays trades in a sortable, filterable table

## Project Structure

```
harpoon/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Environment config
│   │   ├── database.py          # PostgreSQL connection
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── trade.py         # Trade data models
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── trades.py        # Trade endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── polymarket.py    # Polymarket data fetching
│   │   │   ├── subgraph.py      # TheGraph queries
│   │   │   └── polygon.py       # Polygon RPC calls
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── address.py       # Address parsing utilities
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Home page
│   │   │   └── globals.css      # Global styles
│   │   ├── components/
│   │   │   ├── SearchInput.tsx  # Address input component
│   │   │   ├── TradeTable.tsx   # Trade list display
│   │   │   └── TradeRow.tsx     # Individual trade row
│   │   ├── lib/
│   │   │   └── api.ts           # API client
│   │   └── types/
│   │       └── trade.ts         # TypeScript types
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── Dockerfile
│   └── .env.example
├── PLAN.md
├── AGENTS.md
├── README.md
├── docker-compose.yml           # Local development
└── railway.toml                 # Railway deployment config
```

## API Endpoints

### Backend (FastAPI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/trades/{address}` | Get all trades for a wallet address |
| GET | `/api/trades/{address}?page=1&limit=50` | Paginated trades |
| POST | `/api/resolve-profile` | Convert Polymarket profile URL to address |

### Response Schema

```json
{
  "address": "0x...",
  "trades": [
    {
      "id": "tx_hash",
      "timestamp": "2024-01-15T10:30:00Z",
      "market_id": "...",
      "market_title": "Will X happen?",
      "outcome": "Yes",
      "side": "buy",
      "amount": "100.00",
      "price": "0.65",
      "token_id": "...",
      "polygonscan_url": "https://polygonscan.com/tx/..."
    }
  ],
  "total_count": 150,
  "page": 1,
  "limit": 50
}
```

## Database Schema

```sql
-- Cached trades table
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    tx_hash VARCHAR(66) UNIQUE NOT NULL,
    wallet_address VARCHAR(42) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    market_id VARCHAR(255),
    market_title TEXT,
    outcome VARCHAR(10),
    side VARCHAR(4),
    amount DECIMAL(20, 8),
    price DECIMAL(10, 8),
    token_id VARCHAR(255),
    block_number BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_wallet_address (wallet_address),
    INDEX idx_timestamp (timestamp)
);

-- Cache metadata
CREATE TABLE cache_metadata (
    wallet_address VARCHAR(42) PRIMARY KEY,
    last_fetched TIMESTAMPTZ NOT NULL,
    last_block_number BIGINT
);
```

## UI Design Specifications

### Color Palette
- Background: `#F5F0E6` (warm beige)
- Text: `#1A1A1A` (near black)
- Accent: `#2C2C2C` (dark gray)
- Border: `#D4CFC4` (muted beige)
- Hover: `#EBE6DC` (light beige)

### Typography
- Headings: `Georgia, 'Times New Roman', serif`
- Body: `'IBM Plex Mono', 'Courier New', monospace`
- Numbers/Data: `'IBM Plex Mono', monospace`

### Layout
- Max width: 1200px, centered
- Generous whitespace
- Clean table design with subtle borders
- Minimalist input field with underline style

## Implementation Phases

### Phase 1: Project Setup
- [x] Initialize git repository
- [ ] Create project structure
- [ ] Set up backend with FastAPI skeleton
- [ ] Set up frontend with Next.js skeleton
- [ ] Configure local development with Docker Compose

### Phase 2: Backend Core
- [ ] Implement PostgreSQL connection and models
- [ ] Create TheGraph subgraph query service
- [ ] Implement Polygon RPC service for additional data
- [ ] Build trades endpoint with pagination
- [ ] Add profile URL to address resolver

### Phase 3: Frontend Core
- [ ] Implement search input component
- [ ] Build trade table with sorting
- [ ] Add Polygonscan links
- [ ] Implement loading and error states
- [ ] Apply design system (black on beige, formal fonts)

### Phase 4: Integration & Polish
- [ ] Connect frontend to backend API
- [ ] Implement caching strategy
- [ ] Add proper error handling
- [ ] Performance optimization

### Phase 5: Deployment
- [ ] Create Dockerfiles for both services
- [ ] Configure Railway deployment
- [ ] Set up environment variables
- [ ] Deploy and test

## External APIs & Data Sources

### TheGraph Subgraph
- Polymarket uses Conditional Token Framework (CTF)
- Subgraph URL: `https://api.thegraph.com/subgraphs/name/polymarket/polymarket-matic`
- Query for: `fpmmTrades`, `fpmmFundingAdditions`, `transactions`

### Polygon RPC
- Use Alchemy or public Polygon RPC
- For transaction details and timestamps
- Backup for data not in subgraph

### Polymarket Profile Resolution
- Parse profile URLs: `https://polymarket.com/profile/{username}`
- May need to query Polymarket API or on-chain data to resolve username to address

## Environment Variables

### Backend
```
DATABASE_URL=postgresql://user:pass@host:5432/harpoon
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/...
```

### Frontend
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Railway Deployment

Both services will be deployed as separate Railway services:
1. `harpoon-api` - FastAPI backend
2. `harpoon-web` - Next.js frontend
3. `harpoon-db` - PostgreSQL (Railway plugin)

Railway config will use Nixpacks for automatic builds.
