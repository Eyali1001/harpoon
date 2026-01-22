import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.trade import Trade, CacheMetadata, TradeResponse, TradesListResponse, ProfileInfo, TimezoneAnalysis, CategoryStat, InsiderMetrics
from collections import Counter
from app.services.subgraph import fetch_trades_from_subgraph, fetch_profit_from_positions
from app.services.profile import resolve_profile_to_address, fetch_public_profile
from app.utils.address import is_valid_address

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info(f"Processing request for: {address_or_url}")

    try:
        # Resolve profile URL/username to wallet address
        address = await resolve_profile_to_address(address_or_url)
    except Exception as e:
        logger.error(f"Profile resolution error for {address_or_url}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={
            "code": "PROFILE_ERROR",
            "message": f"Failed to resolve profile: {str(e)}"
        })

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
                        market_slug=trade_data.get("market_slug"),
                        outcome=trade_data.get("outcome"),
                        side=trade_data.get("side"),
                        amount=trade_data.get("amount"),
                        price=trade_data.get("price"),
                        token_id=trade_data.get("token_id"),
                        block_number=trade_data.get("block_number"),
                        tags=trade_data.get("tags"),
                        closed=trade_data.get("closed", False),
                        close_time=trade_data.get("close_time"),
                        outcome_won=trade_data.get("outcome_won"),
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
            logger.error(f"SUBGRAPH_ERROR for {address}: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail={
                "code": "SUBGRAPH_ERROR",
                "message": f"Failed to fetch trades: {str(e)}"
            })

    try:
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
    except Exception as e:
        logger.error(f"Database query error for {address}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={
            "code": "DATABASE_ERROR",
            "message": f"Failed to query trades: {str(e)}"
        })

    trade_responses = [
        TradeResponse(
            tx_hash=t.tx_hash,
            timestamp=t.timestamp,
            market_id=t.market_id,
            market_title=t.market_title,
            market_slug=t.market_slug,
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

    # Fetch P/L from positions API (more accurate than trade-based calculation)
    profit_data = await fetch_profit_from_positions(address)
    total_earnings = profit_data["total_pnl"]

    # Get all trades for analytics
    all_trades_result = await db.execute(
        select(
            Trade.side, Trade.amount, Trade.timestamp, Trade.tags,
            Trade.price, Trade.outcome, Trade.closed, Trade.close_time, Trade.outcome_won
        ).where(Trade.wallet_address == address)
    )
    all_trades_data = all_trades_result.all()

    timestamps = []
    tag_counter = Counter()
    tag_pnl = {}  # Track P/L per category (approximation based on trades)

    # Insider metrics tracking
    resolved_buy_trades = []  # (price, outcome_won, hours_before_close)
    trades_within_24h = 0
    trades_within_1h = 0

    for side, amount, timestamp, tags, price, outcome, closed, close_time, outcome_won in all_trades_data:
        if timestamp:
            timestamps.append(timestamp)

        amt = float(amount) if amount else 0
        trade_tags = []
        if tags:
            for tag in tags.split(","):
                tag = tag.strip()
                if tag:
                    tag_counter[tag] += 1
                    trade_tags.append(tag)
                    if tag not in tag_pnl:
                        tag_pnl[tag] = 0.0

        # Calculate approximate P/L per trade for category breakdown
        # (This is an approximation - actual P/L comes from positions API)
        pnl = 0.0
        if side == "buy":
            pnl = -amt
        elif side in ("sell", "redeem"):
            pnl = amt

        # Update P/L per category (approximation)
        for tag in trade_tags:
            tag_pnl[tag] += pnl

        # Track resolved buy trades for insider metrics
        if side == "buy" and closed and outcome_won is not None and price:
            hours_before = None
            if close_time and timestamp:
                try:
                    from datetime import datetime as dt
                    # Parse close_time string (format: "2020-11-02 16:31:01+00")
                    close_dt = dt.fromisoformat(close_time.replace("+00", "+00:00").replace(" ", "T"))
                    trade_dt = timestamp
                    if trade_dt.tzinfo is None:
                        trade_dt = trade_dt.replace(tzinfo=timezone.utc)
                    hours_before = (close_dt - trade_dt).total_seconds() / 3600
                    if hours_before >= 0:
                        if hours_before <= 24:
                            trades_within_24h += 1
                        if hours_before <= 1:
                            trades_within_1h += 1
                except Exception:
                    pass

            resolved_buy_trades.append({
                "price": float(price),
                "won": outcome_won,
                "hours_before": hours_before,
                "outcome": outcome
            })

    # Calculate insider metrics
    insider_metrics = None
    if resolved_buy_trades:
        total_resolved = len(resolved_buy_trades)
        wins = sum(1 for t in resolved_buy_trades if t["won"])
        win_rate = (wins / total_resolved) * 100 if total_resolved > 0 else None

        # Expected win rate = average entry price (buy at 0.3 means 30% expected)
        avg_price = sum(t["price"] for t in resolved_buy_trades) / total_resolved
        expected_win_rate = avg_price * 100

        # Win rate edge
        win_rate_edge = (win_rate - expected_win_rate) if win_rate is not None else None

        # Contrarian trades: betting on unlikely outcome (price < 0.5)
        contrarian_trades = [t for t in resolved_buy_trades if t["price"] < 0.5]
        contrarian_count = len(contrarian_trades)
        contrarian_wins = sum(1 for t in contrarian_trades if t["won"])
        contrarian_win_rate = (contrarian_wins / contrarian_count * 100) if contrarian_count > 0 else None

        # Average hours before close
        hours_list = [t["hours_before"] for t in resolved_buy_trades if t["hours_before"] is not None and t["hours_before"] >= 0]
        avg_hours = sum(hours_list) / len(hours_list) if hours_list else None

        insider_metrics = InsiderMetrics(
            win_rate=round(win_rate, 1) if win_rate is not None else None,
            expected_win_rate=round(expected_win_rate, 1),
            win_rate_edge=round(win_rate_edge, 1) if win_rate_edge is not None else None,
            contrarian_trades=contrarian_count,
            contrarian_wins=contrarian_wins,
            contrarian_win_rate=round(contrarian_win_rate, 1) if contrarian_win_rate is not None else None,
            avg_hours_before_close=round(avg_hours, 1) if avg_hours is not None else None,
            trades_within_24h=trades_within_24h,
            trades_within_1h=trades_within_1h,
            resolved_trades=total_resolved,
            total_trades=len(all_trades_data)
        )

    # Calculate timezone analysis
    tz_analysis = calculate_timezone_analysis(timestamps)

    # Calculate top categories with P/L
    total_tag_count = sum(tag_counter.values())
    top_categories = [
        CategoryStat(
            name=tag,
            count=count,
            percentage=round((count / total_tag_count) * 100, 1) if total_tag_count > 0 else 0,
            pnl=round(tag_pnl.get(tag, 0), 2)
        )
        for tag, count in tag_counter.most_common(10)
    ]

    try:
        return TradesListResponse(
            address=address,
            profile=profile_info,
            trades=trade_responses,
            total_count=total_count,
            page=page,
            limit=limit,
            total_earnings=f"{total_earnings:.2f}",
            timezone_analysis=tz_analysis,
            top_categories=top_categories,
            insider_metrics=insider_metrics
        )
    except Exception as e:
        logger.error(f"Response building error for {address}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={
            "code": "RESPONSE_ERROR",
            "message": f"Failed to build response: {str(e)}"
        })


@router.delete("/trades/{address}")
async def delete_trades_cache(
    address: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete all cached trades and metadata for an address."""
    from sqlalchemy import delete

    address = address.lower()
    logger.info(f"Deleting cache for {address}")

    try:
        # Delete trades
        await db.execute(
            delete(Trade).where(Trade.wallet_address == address)
        )
        # Delete cache metadata
        await db.execute(
            delete(CacheMetadata).where(CacheMetadata.wallet_address == address)
        )
        await db.commit()

        return {"status": "ok", "message": f"Deleted cache for {address}"}
    except Exception as e:
        logger.error(f"Delete error for {address}: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "code": "DELETE_ERROR",
            "message": f"Failed to delete cache: {str(e)}"
        })


@router.delete("/admin/clear-all")
async def clear_all_data(
    db: AsyncSession = Depends(get_db)
):
    """Delete ALL cached trades and metadata from the database."""
    from sqlalchemy import delete

    logger.warning("Clearing ALL data from database")

    try:
        # Delete all trades
        result_trades = await db.execute(delete(Trade))
        # Delete all cache metadata
        result_cache = await db.execute(delete(CacheMetadata))
        await db.commit()

        return {
            "status": "ok",
            "message": "All data cleared",
            "deleted_trades": result_trades.rowcount,
            "deleted_cache_entries": result_cache.rowcount
        }
    except Exception as e:
        logger.error(f"Clear all error: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "code": "CLEAR_ALL_ERROR",
            "message": f"Failed to clear all data: {str(e)}"
        })
