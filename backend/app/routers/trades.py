from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.trade import Trade, CacheMetadata, TradeResponse, TradesListResponse, ProfileInfo
from app.services.subgraph import fetch_trades_from_subgraph
from app.services.profile import resolve_profile_to_address, fetch_public_profile
from app.utils.address import is_valid_address

router = APIRouter()

CACHE_TTL_MINUTES = 5


@router.get("/trades/{address_or_url:path}", response_model=TradesListResponse)
async def get_trades(
    address_or_url: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    # Resolve profile URL/username to wallet address
    address = await resolve_profile_to_address(address_or_url)

    if not address or not is_valid_address(address):
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_ADDRESS",
            "message": "Could not resolve to a valid Ethereum address. Please provide a wallet address or valid Polymarket profile URL."
        })

    address = address.lower()

    cache_result = await db.execute(
        select(CacheMetadata).where(CacheMetadata.wallet_address == address)
    )
    cache_meta = cache_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    should_refresh = cache_meta is None
    if cache_meta is not None:
        # Handle both timezone-aware and naive datetimes (SQLite vs PostgreSQL)
        last_fetched = cache_meta.last_fetched
        if last_fetched.tzinfo is None:
            last_fetched = last_fetched.replace(tzinfo=timezone.utc)
        should_refresh = (now - last_fetched) > timedelta(minutes=CACHE_TTL_MINUTES)

    if should_refresh:
        try:
            new_trades = await fetch_trades_from_subgraph(address)

            for trade_data in new_trades:
                existing = await db.execute(
                    select(Trade).where(Trade.tx_hash == trade_data["tx_hash"])
                )
                if existing.scalar_one_or_none() is None:
                    trade = Trade(
                        tx_hash=trade_data["tx_hash"],
                        wallet_address=address,
                        timestamp=trade_data["timestamp"],
                        market_id=trade_data.get("market_id"),
                        market_title=trade_data.get("market_title"),
                        outcome=trade_data.get("outcome"),
                        side=trade_data.get("side"),
                        amount=trade_data.get("amount"),
                        price=trade_data.get("price"),
                        token_id=trade_data.get("token_id"),
                        block_number=trade_data.get("block_number"),
                    )
                    db.add(trade)

            if cache_meta:
                cache_meta.last_fetched = now
            else:
                cache_meta = CacheMetadata(
                    wallet_address=address,
                    last_fetched=now
                )
                db.add(cache_meta)

            await db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "code": "SUBGRAPH_ERROR",
                "message": f"Failed to fetch trades: {str(e)}"
            })

    count_result = await db.execute(
        select(func.count()).select_from(Trade).where(Trade.wallet_address == address)
    )
    total_count = count_result.scalar()

    offset = (page - 1) * limit
    trades_result = await db.execute(
        select(Trade)
        .where(Trade.wallet_address == address)
        .order_by(Trade.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    trades = trades_result.scalars().all()

    trade_responses = [
        TradeResponse(
            tx_hash=t.tx_hash,
            timestamp=t.timestamp,
            market_id=t.market_id,
            market_title=t.market_title,
            outcome=t.outcome,
            side=t.side,
            amount=str(t.amount) if t.amount else None,
            price=str(t.price) if t.price else None,
            token_id=t.token_id,
            polygonscan_url=f"https://polygonscan.com/tx/{t.tx_hash}"
        )
        for t in trades
    ]

    # Fetch profile info
    profile_data = await fetch_public_profile(address)
    profile_info = None
    if profile_data:
        profile_info = ProfileInfo(
            name=profile_data.get("name"),
            pseudonym=profile_data.get("pseudonym"),
            profile_image=profile_data.get("profile_image"),
            bio=profile_data.get("bio"),
            profile_url=profile_data.get("profile_url"),
        )

    # Calculate total earnings: (sells + redeems) - buys
    all_trades_result = await db.execute(
        select(Trade.side, Trade.amount).where(Trade.wallet_address == address)
    )
    all_trades_data = all_trades_result.all()

    total_earnings = 0.0
    for side, amount in all_trades_data:
        if amount is None:
            continue
        amt = float(amount)
        if side == "buy":
            total_earnings -= amt
        elif side in ("sell", "redeem"):
            total_earnings += amt

    return TradesListResponse(
        address=address,
        profile=profile_info,
        trades=trade_responses,
        total_count=total_count,
        page=page,
        limit=limit,
        total_earnings=f"{total_earnings:.2f}"
    )
