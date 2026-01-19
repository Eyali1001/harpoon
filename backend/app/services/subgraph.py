import httpx
from datetime import datetime, timezone
from app.config import get_settings

settings = get_settings()

TRADES_QUERY = """
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
    type
    fpmm {
      id
      question {
        title
      }
      outcomes
    }
  }
}
"""


async def fetch_trades_from_subgraph(address: str) -> list[dict]:
    all_trades = []
    skip = 0
    batch_size = 100

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.post(
                settings.subgraph_url,
                json={
                    "query": TRADES_QUERY,
                    "variables": {
                        "user": address.lower(),
                        "first": batch_size,
                        "skip": skip
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Subgraph request failed: {response.status_code}")

            data = response.json()

            if "errors" in data:
                raise Exception(f"Subgraph query error: {data['errors']}")

            trades = data.get("data", {}).get("fpmmTrades", [])

            if not trades:
                break

            for trade in trades:
                timestamp = datetime.fromtimestamp(
                    int(trade["creationTimestamp"]),
                    tz=timezone.utc
                )

                outcome_index = int(trade.get("outcomeIndex", 0))
                outcomes = trade.get("fpmm", {}).get("outcomes", [])
                outcome = outcomes[outcome_index] if outcome_index < len(outcomes) else None

                collateral = trade.get("collateralAmount", "0")
                amount = int(collateral) / 1e6 if collateral else 0

                outcome_tokens = trade.get("outcomeTokensTraded", "0")
                tokens = int(outcome_tokens) / 1e18 if outcome_tokens else 0
                price = amount / tokens if tokens > 0 else 0

                trade_type = trade.get("type", "Buy")

                all_trades.append({
                    "tx_hash": trade["transactionHash"],
                    "timestamp": timestamp,
                    "market_id": trade.get("fpmm", {}).get("id"),
                    "market_title": trade.get("fpmm", {}).get("question", {}).get("title"),
                    "outcome": outcome,
                    "side": trade_type.lower() if trade_type else "buy",
                    "amount": amount,
                    "price": round(price, 4) if price else None,
                    "token_id": trade.get("id"),
                    "block_number": None,
                })

            if len(trades) < batch_size:
                break

            skip += batch_size

    return all_trades
