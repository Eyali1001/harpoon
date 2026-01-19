from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.trade import Trade, CacheMetadata, TradeResponse, TradesListResponse, ProfileInfo, TimezoneAnalysis
from app.services.subgraph import fetch_trades_from_subgraph
from app.services.profile import resolve_profile_to_address, fetch_public_profile
from app.utils.address import is_valid_address

router = APIRouter()

CACHE_TTL_MINUTES = 5

# Common timezones with their UTC offsets and typical names
TIMEZONE_MAP = [
    (-12, "Baker Island"),
    (-11, "American Samoa"),
    (-10, "Hawaii"),
    (-9, "Alaska"),
    (-8, "US Pacific"),
    (-7, "US Mountain"),
    (-6, "US Central"),
    (-5, "US Eastern"),
    (-4, "Atlantic"),
    (-3, "Brazil/Argentina"),
    (-2, "Mid-Atlantic"),
    (-1, "Azores"),
    (0, "UK/Portugal"),
    (1, "Central Europe"),
    (2, "Eastern Europe"),
    (3, "Moscow/Arabia"),
    (4, "Gulf/Caucasus"),
    (5, "Pakistan/West Asia"),
    (5.5, "India"),
    (6, "Bangladesh"),
    (7, "Indochina"),
    (8, "China/Singapore"),
    (9, "Japan/Korea"),
    (10, "Australia East"),
    (11, "Pacific Islands"),
    (12, "New Zealand"),
]


def calculate_timezone_analysis(timestamps: list[datetime]) -> TimezoneAnalysis:
    """Calculate hourly distribution and infer timezone from trade timestamps."""
    if not timestamps:
        return TimezoneAnalysis(
            hourly_distribution=[0] * 24,
            inferred_timezone=None,
            inferred_utc_offset=None,
            activity_center_utc=None
        )

    # Calculate hourly distribution (UTC)
    hourly_counts = [0] * 24
    for ts in timestamps:
        hour = ts.hour
        hourly_counts[hour] += 1

    # Calculate activity center (weighted circular mean for hours)
    # Using circular statistics to handle the 23->0 wrap-around
    import math
    total_weight = sum(hourly_counts)
    if total_weight == 0:
        return TimezoneAnalysis(
            hourly_distribution=hourly_counts,
            inferred_timezone=None,
            inferred_utc_offset=None,
            activity_center_utc=None
        )

    sin_sum = 0
    cos_sum = 0
    for hour, count in enumerate(hourly_counts):
        angle = 2 * math.pi * hour / 24
        sin_sum += count * math.sin(angle)
        cos_sum += count * math.cos(angle)

    avg_angle = math.atan2(sin_sum, cos_sum)
    if avg_angle < 0:
        avg_angle += 2 * math.pi
    activity_center_utc = (avg_angle * 24) / (2 * math.pi)

    # Infer timezone: assume activity center should be around 3pm local (15:00)
    # So UTC offset = 15 - activity_center_utc
    target_local_hour = 15  # 3pm - middle of typical active day
    utc_offset = target_local_hour - activity_center_utc

    # Normalize to -12 to +12 range
    if utc_offset > 12:
        utc_offset -= 24
    elif utc_offset < -12:
        utc_offset += 24

    # Round to nearest half hour for timezone matching
    utc_offset_rounded = round(utc_offset * 2) / 2

    # Find closest timezone
    closest_tz = min(TIMEZONE_MAP, key=lambda tz: abs(tz[0] - utc_offset_rounded))

    return TimezoneAnalysis(
        hourly_distribution=hourly_counts,
        inferred_timezone=closest_tz[1],
        inferred_utc_offset=int(closest_tz[0]) if closest_tz[0] == int(closest_tz[0]) else closest_tz[0],
        activity_center_utc=round(activity_center_utc, 1)
    )


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
        select(Trade.side, Trade.amount, Trade.timestamp).where(Trade.wallet_address == address)
    )
    all_trades_data = all_trades_result.all()

    total_earnings = 0.0
    timestamps = []
    for side, amount, timestamp in all_trades_data:
        if timestamp:
            timestamps.append(timestamp)
        if amount is None:
            continue
        amt = float(amount)
        if side == "buy":
            total_earnings -= amt
        elif side in ("sell", "redeem"):
            total_earnings += amt

    # Calculate timezone analysis
    tz_analysis = calculate_timezone_analysis(timestamps)

    return TradesListResponse(
        address=address,
        profile=profile_info,
        trades=trade_responses,
        total_count=total_count,
        page=page,
        limit=limit,
        total_earnings=f"{total_earnings:.2f}",
        timezone_analysis=tz_analysis
    )
