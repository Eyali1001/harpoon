import httpx
import logging
from datetime import datetime, timezone
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


async def fetch_profit_from_positions(address: str) -> dict:
    """Fetch P/L from Polymarket positions API.

    Note: This only shows current/recent positions. For historical P/L,
    we need to calculate from trade history.
    """
    result = {"realized_pnl": 0.0, "unrealized_pnl": 0.0, "total_pnl": 0.0}
    address = address.lower()

    async with httpx.AsyncClient() as client:
        offset = 0
        while offset < 10000:
            try:
                response = await client.get(
                    "https://data-api.polymarket.com/positions",
                    params={"user": address, "limit": 100, "offset": offset},
                    timeout=30.0
                )

                if response.status_code != 200:
                    break

                positions = response.json()
                if not positions:
                    break

                for pos in positions:
                    # realizedPnl includes P/L from partial closes
                    result["realized_pnl"] += float(pos.get("realizedPnl") or 0)
                    # cashPnl = currentValue - initialValue (unrealized)
                    result["unrealized_pnl"] += float(pos.get("cashPnl") or 0)

                if len(positions) < 100:
                    break
                offset += 100

            except Exception as e:
                logger.error(f"Positions API error: {e}")
                break

    result["total_pnl"] = result["realized_pnl"] + result["unrealized_pnl"]
    logger.info(f"P/L for {address}: realized={result['realized_pnl']:.2f}, unrealized={result['unrealized_pnl']:.2f}")
    return result


async def fetch_event_info_by_slug(client: httpx.AsyncClient, event_slug: str) -> dict:
    """Fetch event info including tags from Gamma API."""
    result = {"tags": []}
    try:
        response = await client.get(
            f"{settings.gamma_api_url}/events/slug/{event_slug}",
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            tags = data.get("tags", [])
            result["tags"] = [tag.get("label") for tag in tags if tag.get("label")]
    except Exception:
        pass
    return result


async def fetch_market_info_by_slug(client: httpx.AsyncClient, market_slug: str) -> dict:
    """Fetch market info including resolution status from Gamma API."""
    result = {"closed": False, "close_time": None, "outcome_prices": {}}
    try:
        response = await client.get(
            f"{settings.gamma_api_url}/markets",
            params={"slug": market_slug},
            timeout=10.0
        )
        if response.status_code == 200:
            markets = response.json()
            if markets:
                market = markets[0]
                result["closed"] = market.get("closed", False)
                result["close_time"] = market.get("closedTime")
                # Parse outcome prices to determine winner
                import json
                outcomes_str = market.get("outcomes", "[]")
                prices_str = market.get("outcomePrices", "[]")
                try:
                    outcomes = json.loads(outcomes_str) if isinstance(outcomes_str, str) else outcomes_str
                    prices = json.loads(prices_str) if isinstance(prices_str, str) else prices_str
                    for i, outcome in enumerate(outcomes):
                        if i < len(prices):
                            result["outcome_prices"][outcome] = float(prices[i])
                except:
                    pass
    except Exception as e:
        logger.debug(f"Failed to fetch market info for {market_slug}: {e}")
    return result


async def fetch_trades_from_data_api(address: str) -> list[dict]:
    """Fetch trades from Polymarket Data API."""
    all_trades = []
    raw_trades = []
    address = address.lower()
    event_slugs = set()
    market_slugs = set()

    async with httpx.AsyncClient() as client:
        offset = 0
        max_trades = 5000  # Safety limit
        while offset < max_trades:
            params = {"user": address, "limit": 100, "offset": offset}

            try:
                response = await client.get(
                    "https://data-api.polymarket.com/trades",
                    params=params,
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.warning(f"Data API returned {response.status_code}")
                    break

                trades = response.json()
                if not trades:
                    break

                for trade in trades:
                    raw_trades.append(trade)
                    event_slug = trade.get("eventSlug")
                    market_slug = trade.get("slug")
                    if event_slug:
                        event_slugs.add(event_slug)
                    if market_slug:
                        market_slugs.add(market_slug)

                # Check for next page
                if len(trades) < 100:
                    break
                offset += 100

            except Exception as e:
                logger.error(f"Data API error: {e}")
                break

        logger.info(f"Fetched {len(raw_trades)} raw trades for {address}")

        # Fetch tags and market info concurrently
        import asyncio
        event_info_cache = {}
        market_info_cache = {}
        semaphore = asyncio.Semaphore(10)

        async def fetch_event_with_semaphore(slug):
            async with semaphore:
                info = await fetch_event_info_by_slug(client, slug)
                return slug, info

        async def fetch_market_with_semaphore(slug):
            async with semaphore:
                info = await fetch_market_info_by_slug(client, slug)
                return slug, info

        # Fetch event info (for tags)
        if event_slugs:
            results = await asyncio.gather(*[fetch_event_with_semaphore(slug) for slug in list(event_slugs)[:50]])
            for slug, info in results:
                event_info_cache[slug] = info

        # Fetch market info (for resolution status)
        if market_slugs:
            results = await asyncio.gather(*[fetch_market_with_semaphore(slug) for slug in list(market_slugs)[:50]])
            for slug, info in results:
                market_info_cache[slug] = info

        # Process trades with tags and market resolution
        for trade in raw_trades:
            # timestamp is unix epoch integer
            ts = trade.get("timestamp")
            if isinstance(ts, int):
                timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)
            else:
                timestamp = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))

            # side is uppercase BUY/SELL
            side = trade.get("side", "").lower()
            if side not in ("buy", "sell"):
                side = "buy"

            # Get market info
            outcome = trade.get("outcome", "")
            title = trade.get("title") or trade.get("slug", "")
            event_slug = trade.get("eventSlug")
            market_slug = trade.get("slug")

            # Get tags from event info
            event_info = event_info_cache.get(event_slug, {})
            tags = event_info.get("tags", [])

            # Get market resolution status
            market_info = market_info_cache.get(market_slug, {})
            is_closed = market_info.get("closed", False)
            close_time = market_info.get("close_time")
            outcome_prices = market_info.get("outcome_prices", {})

            # Determine if this outcome won (price > 0.99 means it won)
            outcome_won = None
            if is_closed and outcome and outcome in outcome_prices:
                outcome_won = outcome_prices[outcome] > 0.99

            # Calculate amount (size * price)
            size = float(trade.get("size", 0))
            price = float(trade.get("price", 0))
            amount = size * price

            all_trades.append({
                "tx_hash": trade.get("transactionHash") or f"data-api-{trade.get('timestamp', '')}",
                "timestamp": timestamp,
                "market_id": trade.get("conditionId") or market_slug,
                "market_title": title,
                "market_slug": event_slug or market_slug,  # Use event slug for Polymarket URLs
                "outcome": outcome,
                "side": side,
                "amount": round(amount, 2),
                "price": round(price, 4) if price else None,
                "token_id": trade.get("asset"),
                "block_number": None,
                "tags": ",".join(tags) if tags else None,
                "closed": is_closed,
                "close_time": close_time,
                "outcome_won": outcome_won,
            })

    logger.info(f"Fetched {len(all_trades)} trades from Data API for {address}")
    return all_trades


async def fetch_trades_from_subgraph(address: str) -> list[dict]:
    """Fetch all trades for an address from Data API and subgraphs."""
    all_trades = []
    address = address.lower()

    # First try the Data API (more complete data)
    data_api_trades = await fetch_trades_from_data_api(address)
    if data_api_trades:
        return data_api_trades

    # Fall back to subgraphs if Data API returns nothing
    logger.info("Data API returned no trades, trying subgraphs...")

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

            # Log first fill to see structure
            if maker_fills:
                logger.info(f"Sample maker fill keys: {list(maker_fills[0].keys())}")
            if taker_fills:
                logger.info(f"Sample taker fill keys: {list(taker_fills[0].keys())}")

            for fill in maker_fills + taker_fills:
                timestamp = datetime.fromtimestamp(int(fill["timestamp"]), tz=timezone.utc)
                tx_hash = fill.get("transactionHash") or fill.get("txHash") or fill.get("id", "").split("-")[0]

                # Determine if this is a buy or sell based on asset IDs
                # Asset ID 0 = USDC, non-zero = outcome token
                maker_asset = fill.get("makerAssetId") or fill.get("makerAsset") or "0"
                taker_asset = fill.get("takerAssetId") or fill.get("takerAsset") or "0"

                # Check for maker/taker fields with different possible names
                maker_addr = fill.get("maker") or fill.get("makerAddress") or ""
                is_user_maker = maker_addr.lower() == address if maker_addr else (fill in maker_fills)

                # Get amounts with fallbacks for different field names
                maker_amount = int(fill.get("makerAmountFilled") or fill.get("makerAmount") or 0) / 1e6
                taker_amount = int(fill.get("takerAmountFilled") or fill.get("takerAmount") or 0) / 1e6

                if is_user_maker:
                    if maker_asset == "0":
                        # User is maker, giving USDC = buying outcome tokens
                        side = "buy"
                        token_id = taker_asset
                        amount = maker_amount
                        tokens = taker_amount
                    else:
                        # User is maker, giving tokens = selling
                        side = "sell"
                        token_id = maker_asset
                        tokens = maker_amount
                        amount = taker_amount
                else:
                    if taker_asset == "0":
                        # User is taker, giving USDC = buying
                        side = "buy"
                        token_id = maker_asset
                        amount = taker_amount
                        tokens = maker_amount
                    else:
                        # User is taker, giving tokens = selling
                        side = "sell"
                        token_id = taker_asset
                        tokens = taker_amount
                        amount = maker_amount

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
