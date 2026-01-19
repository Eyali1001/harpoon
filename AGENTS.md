# AGENTS.md - AI Development Guidelines for Harpoon

## Project Context

Harpoon is a Polymarket trade viewer that displays all trades for a given wallet address or Polymarket profile URL. The app shows trade history with timestamps and Polygonscan links.

## Tech Stack Reference

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: Next.js 14 with TypeScript
- **Database**: PostgreSQL
- **Data Sources**: Polygon RPC + TheGraph Subgraph
- **Deployment**: Railway

## Code Style Guidelines

### Python (Backend)

```python
# Use async/await for all I/O operations
async def get_trades(address: str) -> list[Trade]:
    ...

# Use Pydantic models for request/response validation
class TradeResponse(BaseModel):
    tx_hash: str
    timestamp: datetime
    amount: Decimal

# Use dependency injection for database sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    ...
```

### TypeScript (Frontend)

```typescript
// Use named exports
export function TradeTable({ trades }: TradeTableProps) { ... }

// Define types explicitly
interface Trade {
  id: string;
  timestamp: string;
  amount: string;
}

// Use async/await for API calls
const trades = await fetchTrades(address);
```

## Key Implementation Details

### Address Resolution

Polymarket profile URLs follow the pattern:
- `https://polymarket.com/profile/{username_or_address}`

The backend must:
1. Detect if input is already a valid Ethereum address (0x...)
2. If URL, extract the identifier and resolve to address
3. Validate the address format before querying

### Subgraph Queries

The Polymarket subgraph uses Conditional Token Framework. Key entities:
- `User` - wallet addresses that have interacted
- `Transaction` - on-chain transactions
- `FpmmTrade` - trades on Fixed Product Market Makers

Example query structure:
```graphql
query GetTrades($user: String!, $first: Int!, $skip: Int!) {
  fpmmTrades(
    where: { creator: $user }
    orderBy: creationTimestamp
    orderDirection: desc
    first: $first
    skip: $skip
  ) {
    id
    creationTimestamp
    transactionHash
    outcomeIndex
    outcomeTokensTraded
    collateralAmount
    feeAmount
    fpmm {
      id
      conditions {
        id
      }
    }
  }
}
```

### Database Caching Strategy

1. On first request for an address, fetch all trades from subgraph
2. Store trades in PostgreSQL with `wallet_address` index
3. Track `last_fetched` timestamp in `cache_metadata`
4. On subsequent requests:
   - If cache < 5 minutes old, return cached data
   - Otherwise, fetch only new trades (after last block number)

### UI Component Hierarchy

```
App
├── Header (logo, minimal nav)
├── SearchSection
│   └── SearchInput (address/URL input)
├── ResultsSection
│   ├── AddressSummary (total trades, total volume)
│   └── TradeTable
│       └── TradeRow (timestamp, market, outcome, amount, link)
└── Footer (minimal)
```

## API Error Handling

Return consistent error responses:

```json
{
  "error": {
    "code": "INVALID_ADDRESS",
    "message": "The provided address is not a valid Ethereum address"
  }
}
```

Error codes:
- `INVALID_ADDRESS` - Malformed address
- `ADDRESS_NOT_FOUND` - No trades found for address
- `SUBGRAPH_ERROR` - Failed to query subgraph
- `RATE_LIMITED` - Too many requests

## Environment Setup

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Database (via Docker)
docker-compose up -d postgres
```

### Required Environment Variables

Backend `.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/harpoon
POLYGON_RPC_URL=https://polygon-rpc.com
SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/polymarket/polymarket-matic
```

Frontend `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Common Tasks

### Adding a New Endpoint

1. Create route in `backend/app/routers/`
2. Add Pydantic models in `backend/app/models/`
3. Register router in `backend/app/main.py`
4. Update frontend API client in `frontend/src/lib/api.ts`

### Adding a New Frontend Component

1. Create component in `frontend/src/components/`
2. Use the design tokens (beige background, black text, serif headings)
3. Export from component file
4. Import and use in page

### Modifying Database Schema

1. Update SQLAlchemy model in `backend/app/models/`
2. Create migration (if using Alembic)
3. Update Pydantic response models if needed

## Testing Approach

- Backend: pytest with async support
- Frontend: Jest + React Testing Library
- E2E: Playwright (future)

## Deployment Checklist

- [ ] All environment variables set in Railway
- [ ] Database migrations applied
- [ ] CORS configured for production domain
- [ ] Health check endpoints working
- [ ] Frontend API URL pointing to production backend
