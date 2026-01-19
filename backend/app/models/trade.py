from sqlalchemy import Column, String, Integer, BigInteger, DECIMAL, DateTime, Index
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), unique=True, nullable=False)
    wallet_address = Column(String(42), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    market_id = Column(String(255))
    market_title = Column(String)
    outcome = Column(String(10))
    side = Column(String(4))
    amount = Column(DECIMAL(20, 8))
    price = Column(DECIMAL(10, 8))
    token_id = Column(String(255))
    block_number = Column(BigInteger)
    tags = Column(String)  # Comma-separated tags
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CacheMetadata(Base):
    __tablename__ = "cache_metadata"

    wallet_address = Column(String(42), primary_key=True)
    last_fetched = Column(DateTime(timezone=True), nullable=False)
    last_block_number = Column(BigInteger)


class TradeResponse(BaseModel):
    tx_hash: str
    timestamp: datetime
    market_id: str | None
    market_title: str | None
    outcome: str | None
    side: str | None
    amount: str | None
    price: str | None
    token_id: str | None
    polygonscan_url: str

    class Config:
        from_attributes = True


class ProfileInfo(BaseModel):
    name: str | None
    pseudonym: str | None
    profile_image: str | None
    bio: str | None
    profile_url: str | None


class TimezoneAnalysis(BaseModel):
    hourly_distribution: list[int]
    inferred_timezone: str | None
    inferred_utc_offset: int | None
    activity_center_utc: float | None


class CategoryStat(BaseModel):
    name: str
    count: int
    percentage: float


class TradesListResponse(BaseModel):
    address: str
    profile: ProfileInfo | None
    trades: list[TradeResponse]
    total_count: int
    page: int
    limit: int
    total_earnings: str | None
    timezone_analysis: TimezoneAnalysis | None
    top_categories: list[CategoryStat]
