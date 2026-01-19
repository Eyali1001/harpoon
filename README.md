# Harpoon

Polymarket trade viewer - view all trades for any wallet address or Polymarket profile.

## Features

- Input Polymarket profile URL or Polygon wallet address
- View all trades with exact timestamps
- Links to Polygonscan for transaction details
- Pagination for large trade histories
- Clean, minimalist black-on-beige design

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Database**: PostgreSQL
- **Data Sources**: Polygon RPC + TheGraph Subgraph

## Local Development

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)

### Quick Start

```bash
# Start all services
docker-compose up -d

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Development Mode

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
```

## Deployment (Railway)

1. Create a new Railway project
2. Add PostgreSQL plugin
3. Deploy backend service from `/backend`
4. Deploy frontend service from `/frontend`
5. Set environment variables:
   - Backend: `DATABASE_URL`, `POLYGON_RPC_URL`, `SUBGRAPH_URL`
   - Frontend: `NEXT_PUBLIC_API_URL` (point to backend URL)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/trades/{address}` | Get trades for wallet |
| GET | `/api/trades/{address}?page=1&limit=50` | Paginated trades |

## License

MIT
