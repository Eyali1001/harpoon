import httpx
from datetime import datetime, timezone
from app.config import get_settings

settings = get_settings()

# Query for CLOB order fills (trades on the orderbook)
ORDER_FILLS_QUERY = """
query GetOrderFills($user: String!, $first: Int!, $skip: Int!) {
  makerFills: orderFilledEvents(
    where: { maker: $user }
    orderBy: timestamp
    orderDirection: desc
    first: $first
    skip: $skip
  ) {
    id
    timestamp
    transactionHash
    maker
    taker
    makerAssetId
    takerAssetId
    makerAmountFilled
    takerAmountFilled
  }
  takerFills: orderFilledEvents(
    where: { taker: $user }
    orderBy: timestamp
    orderDirection: desc
    first: $first
    skip: $skip
  ) {
    id
    timestamp
    transactionHash
    maker
    taker
    makerAssetId
    takerAssetId
    makerAmountFilled
    takerAmountFilled
  }
}
"""

# Query for on-chain activity (splits = buy, merges = sell, redemptions = claim)
ACTIVITY_QUERY = """
query GetActivity($user: String!, $first: Int!, $skip: Int!) {
  splits(
    where: { stakeholder: $user }
    orderBy: timestamp
    orderDirection: desc
    first: $first
    skip: $skip
  ) {
    id
    timestamp
    stakeholder
    amount
    condition
  }
  merges(
    where: { stakeholder: $user }
    orderBy: timestamp
    orderDirection: desc
    first: $first
    skip: $skip
  ) {
    id
    timestamp
    stakeholder
    amount
    condition
  }
  redemptions(
    where: { redeemer: $user }
    orderBy: timestamp
    orderDirection: desc
    first: $first
    skip: $skip
  ) {
    id
    timestamp
    redeemer
    payout
    condition
  }
}
"""


async def fetch_event_tags(client: httpx.AsyncClient, event_id: str) -> list[str]:
    """Fetch tags for an event."""
    try:
        response = await client.get(
            f"{settings.gamma_api_url}/events/{event_id}",
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                data = data[0] if data else {}
            tags = data.get("tags", [])
            return [tag.get("label") for tag in tags if tag.get("label")]
    except Exception:
        pass
    return []


async def fetch_single_market_by_token(client: httpx.AsyncClient, token_id: str) -> tuple[str, dict | None]:
    """Fetch market info for a single token ID."""
    import json
    try:
        response = await client.get(
            f"{settings.gamma_api_url}/markets",
            params={"clob_token_ids": token_id},
            timeout=10.0
        )
        if response.status_code == 200:
            markets = response.json()
            if markets:
                market = markets[0]
                # Determine which outcome this token represents
                # outcomes and clobTokenIds are JSON strings like '["Yes", "No"]'
                outcome = None
                outcome_won = None
                try:
                    outcomes_str = market.get("outcomes", "[]")
                    token_ids_str = market.get("clobTokenIds", "[]")
                    outcome_prices_str = market.get("outcomePrices", "[]")
                    outcomes_list = json.loads(outcomes_str) if isinstance(outcomes_str, str) else outcomes_str
                    token_ids_list = json.loads(token_ids_str) if isinstance(token_ids_str, str) else token_ids_str
                    outcome_prices_list = json.loads(outcome_prices_str) if isinstance(outcome_prices_str, str) else outcome_prices_str

                    # Find the index of our token_id and get corresponding outcome
                    if token_id in token_ids_list:
                        idx = token_ids_list.index(token_id)
                        if idx < len(outcomes_list):
                            outcome = outcomes_list[idx]
                        # Check if this outcome won (price = "1" means it won)
                        if idx < len(outcome_prices_list) and market.get("closed"):
                            try:
                                outcome_won = float(outcome_prices_list[idx]) == 1.0
                            except (ValueError, TypeError):
                                pass
                except (json.JSONDecodeError, ValueError):
                    pass

                # Get event tags
                tags = []
                events = market.get("events", [])
                if events:
                    event_id = events[0].get("id")
                    if event_id:
                        tags = await fetch_event_tags(client, event_id)

                # Parse close time if market is closed
                close_time = None
                if market.get("closed") and market.get("closedTime"):
                    try:
                        close_time = market.get("closedTime")
                    except Exception:
                        pass

                return token_id, {
                    "question": market.get("question"),
                    "outcomes": market.get("outcomes"),
                    "condition_id": market.get("conditionId"),
                    "outcome": outcome,
                    "tags": tags,
                    "closed": market.get("closed", False),
                    "close_time": close_time,
                    "outcome_won": outcome_won
                }
    except Exception:
        pass
    return token_id, None


async def fetch_single_market_by_condition(client: httpx.AsyncClient, condition_id: str) -> tuple[str, dict | None]:
    """Fetch market info for a single condition ID."""
    try:
        response = await client.get(
            f"{settings.gamma_api_url}/markets",
            params={"condition_ids": condition_id},
            timeout=10.0
        )
        if response.status_code == 200:
            markets = response.json()
            if markets:
                market = markets[0]
                return condition_id, {
                    "question": market.get("question"),
                    "outcomes": market.get("outcomes")
                }
    except Exception:
        pass
    return condition_id, None


async def fetch_market_info(client: httpx.AsyncClient, token_ids: list[str]) -> dict[str, dict]:
    """Fetch market info from Gamma API by token IDs (one at a time, concurrently)."""
    import asyncio
    market_cache = {}

    # Limit concurrent requests
    semaphore = asyncio.Semaphore(5)

    async def fetch_with_semaphore(tid):
        async with semaphore:
            return await fetch_single_market_by_token(client, tid)

    # Fetch all in parallel with rate limiting
    results = await asyncio.gather(*[fetch_with_semaphore(tid) for tid in token_ids])

    for tid, info in results:
        if info:
            market_cache[tid] = info

    return market_cache


async def fetch_market_info_by_condition(client: httpx.AsyncClient, condition_ids: list[str]) -> dict[str, dict]:
    """Fetch market info from Gamma API by condition IDs (one at a time, concurrently)."""
    import asyncio
    market_cache = {}

    # Limit concurrent requests
    semaphore = asyncio.Semaphore(5)

    async def fetch_with_semaphore(cid):
        async with semaphore:
            return await fetch_single_market_by_condition(client, cid)

    # Fetch all in parallel with rate limiting
    results = await asyncio.gather(*[fetch_with_semaphore(cid) for cid in condition_ids])

    for cid, info in results:
        if info:
            market_cache[cid] = info

    return market_cache


async def fetch_trades_from_subgraph(address: str) -> list[dict]:
    """Fetch all trades for an address from multiple subgraphs."""
    all_trades = []
    address = address.lower()

    async with httpx.AsyncClient() as client:
        # Fetch CLOB order fills
        skip = 0
        batch_size = 100
        token_ids_to_lookup = set()

        while True:
            response = await client.post(
                settings.orders_subgraph_url,
                json={
                    "query": ORDER_FILLS_QUERY,
                    "variables": {
                        "user": address,
                        "first": batch_size,
                        "skip": skip
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                break

            data = response.json()
            if "errors" in data:
                break

            maker_fills = data.get("data", {}).get("makerFills", [])
            taker_fills = data.get("data", {}).get("takerFills", [])

            if not maker_fills and not taker_fills:
                break

            for fill in maker_fills + taker_fills:
                timestamp = datetime.fromtimestamp(int(fill["timestamp"]), tz=timezone.utc)
                tx_hash = fill["transactionHash"]

                # Determine if this is a buy or sell based on asset IDs
                # Asset ID 0 = USDC, non-zero = outcome token
                maker_asset = fill["makerAssetId"]
                taker_asset = fill["takerAssetId"]
                is_user_maker = fill["maker"].lower() == address

                if is_user_maker:
                    if maker_asset == "0":
                        # User is maker, giving USDC = buying outcome tokens
                        side = "buy"
                        token_id = taker_asset
                        amount = int(fill["makerAmountFilled"]) / 1e6
                        tokens = int(fill["takerAmountFilled"]) / 1e6
                    else:
                        # User is maker, giving tokens = selling
                        side = "sell"
                        token_id = maker_asset
                        tokens = int(fill["makerAmountFilled"]) / 1e6
                        amount = int(fill["takerAmountFilled"]) / 1e6
                else:
                    if taker_asset == "0":
                        # User is taker, giving USDC = buying
                        side = "buy"
                        token_id = maker_asset
                        amount = int(fill["takerAmountFilled"]) / 1e6
                        tokens = int(fill["makerAmountFilled"]) / 1e6
                    else:
                        # User is taker, giving tokens = selling
                        side = "sell"
                        token_id = taker_asset
                        tokens = int(fill["takerAmountFilled"]) / 1e6
                        amount = int(fill["makerAmountFilled"]) / 1e6

                price = amount / tokens if tokens > 0 else 0

                if token_id != "0":
                    token_ids_to_lookup.add(token_id)

                all_trades.append({
                    "tx_hash": tx_hash,
                    "timestamp": timestamp,
                    "market_id": None,
                    "market_title": None,
                    "outcome": None,
                    "side": side,
                    "amount": round(amount, 2),
                    "price": round(price, 4) if price else None,
                    "token_id": token_id if token_id != "0" else None,
                    "block_number": None,
                    "tags": None,
                    "_source": "clob"
                })

            if len(maker_fills) < batch_size and len(taker_fills) < batch_size:
                break
            skip += batch_size

        # Fetch market info for token IDs
        if token_ids_to_lookup:
            market_cache = await fetch_market_info(client, list(token_ids_to_lookup))
            for trade in all_trades:
                if trade.get("token_id") and trade["token_id"] in market_cache:
                    info = market_cache[trade["token_id"]]
                    trade["market_title"] = info.get("question")
                    trade["market_id"] = info.get("condition_id")
                    trade["outcome"] = info.get("outcome")
                    trade["tags"] = ",".join(info.get("tags", [])) if info.get("tags") else None
                    trade["closed"] = info.get("closed", False)
                    trade["close_time"] = info.get("close_time")
                    trade["outcome_won"] = info.get("outcome_won")

        # Fetch activity (splits, merges, redemptions)
        skip = 0
        condition_ids_to_lookup = set()

        while True:
            response = await client.post(
                settings.activity_subgraph_url,
                json={
                    "query": ACTIVITY_QUERY,
                    "variables": {
                        "user": address,
                        "first": batch_size,
                        "skip": skip
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                break

            data = response.json()
            if "errors" in data:
                break

            splits = data.get("data", {}).get("splits", [])
            merges = data.get("data", {}).get("merges", [])
            redemptions = data.get("data", {}).get("redemptions", [])

            if not splits and not merges and not redemptions:
                break

            for split in splits:
                timestamp = datetime.fromtimestamp(int(split["timestamp"]), tz=timezone.utc)
                # ID format: txhash_logindex
                tx_hash = split["id"].split("_")[0]
                condition_id = split.get("condition")
                amount = int(split["amount"]) / 1e6

                if condition_id:
                    condition_ids_to_lookup.add(condition_id)

                all_trades.append({
                    "tx_hash": tx_hash,
                    "timestamp": timestamp,
                    "market_id": condition_id,
                    "market_title": None,
                    "outcome": None,
                    "side": "buy",
                    "amount": round(amount, 2),
                    "price": None,
                    "token_id": None,
                    "block_number": None,
                    "tags": None,
                    "_source": "split"
                })

            for merge in merges:
                timestamp = datetime.fromtimestamp(int(merge["timestamp"]), tz=timezone.utc)
                tx_hash = merge["id"].split("_")[0]
                condition_id = merge.get("condition")
                amount = int(merge["amount"]) / 1e6

                if condition_id:
                    condition_ids_to_lookup.add(condition_id)

                all_trades.append({
                    "tx_hash": tx_hash,
                    "timestamp": timestamp,
                    "market_id": condition_id,
                    "market_title": None,
                    "outcome": None,
                    "side": "sell",
                    "amount": round(amount, 2),
                    "price": None,
                    "token_id": None,
                    "block_number": None,
                    "tags": None,
                    "_source": "merge"
                })

            for redemption in redemptions:
                timestamp = datetime.fromtimestamp(int(redemption["timestamp"]), tz=timezone.utc)
                tx_hash = redemption["id"].split("_")[0]
                condition_id = redemption.get("condition")
                payout = int(redemption["payout"]) / 1e6

                if condition_id:
                    condition_ids_to_lookup.add(condition_id)

                all_trades.append({
                    "tx_hash": tx_hash,
                    "timestamp": timestamp,
                    "market_id": condition_id,
                    "market_title": None,
                    "outcome": None,
                    "side": "redeem",
                    "amount": round(payout, 2),
                    "price": None,
                    "token_id": None,
                    "block_number": None,
                    "tags": None,
                    "_source": "redemption"
                })

            if len(splits) < batch_size and len(merges) < batch_size and len(redemptions) < batch_size:
                break
            skip += batch_size

        # Fetch market info for condition IDs
        if condition_ids_to_lookup:
            condition_cache = await fetch_market_info_by_condition(client, list(condition_ids_to_lookup))
            for trade in all_trades:
                if trade.get("market_id") and trade["market_id"] in condition_cache and not trade.get("market_title"):
                    info = condition_cache[trade["market_id"]]
                    trade["market_title"] = info.get("question")

    # Remove internal fields and sort by timestamp
    for trade in all_trades:
        trade.pop("_source", None)

    all_trades.sort(key=lambda x: x["timestamp"], reverse=True)

    return all_trades
