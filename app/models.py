from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(unique=True, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    holdings: List["StockHolding"] = Relationship(back_populates="user")


class StockHolding(SQLModel, table=True):
    __tablename__ = "stock_holdings"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(max_length=10, description="Stock ticker symbol (e.g., AAPL, GOOGL)")
    shares: Decimal = Field(ge=0, description="Number of shares owned")
    purchase_price: Decimal = Field(ge=0, description="Original purchase price per share")
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="holdings")

    @property
    def total_purchase_value(self) -> Decimal:
        """Calculate total purchase value (shares * purchase_price)"""
        return self.shares * self.purchase_price


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    email: str = Field(max_length=255)


class StockHoldingCreate(SQLModel, table=False):
    ticker: str = Field(max_length=10, description="Stock ticker symbol (e.g., AAPL, GOOGL)")
    shares: Decimal = Field(ge=0, description="Number of shares owned")
    purchase_price: Decimal = Field(ge=0, description="Original purchase price per share")
    user_id: int


class StockHoldingUpdate(SQLModel, table=False):
    ticker: Optional[str] = Field(default=None, max_length=10)
    shares: Optional[Decimal] = Field(default=None, ge=0)
    purchase_price: Optional[Decimal] = Field(default=None, ge=0)


class PortfolioSummary(SQLModel, table=False):
    """Summary of portfolio performance"""

    total_current_value: Decimal = Field(default=Decimal("0"))
    total_purchase_value: Decimal = Field(default=Decimal("0"))
    total_gain_loss: Decimal = Field(default=Decimal("0"))
    total_gain_loss_percent: Decimal = Field(default=Decimal("0"))
    holdings_count: int = Field(default=0)


class HoldingWithCurrentPrice(SQLModel, table=False):
    """Stock holding with current market data"""

    id: int
    ticker: str
    shares: Decimal
    purchase_price: Decimal
    current_price: Decimal = Field(default=Decimal("0"))
    current_value: Decimal = Field(default=Decimal("0"))
    gain_loss: Decimal = Field(default=Decimal("0"))
    gain_loss_percent: Decimal = Field(default=Decimal("0"))
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_holding(cls, holding: StockHolding, current_price: Decimal) -> "HoldingWithCurrentPrice":
        """Create instance from StockHolding with current price data"""
        if holding.id is None:
            raise ValueError("StockHolding ID cannot be None")

        current_value = holding.shares * current_price
        purchase_value = holding.total_purchase_value
        gain_loss = current_value - purchase_value
        gain_loss_percent = (gain_loss / purchase_value * Decimal("100")) if purchase_value > 0 else Decimal("0")

        return cls(
            id=holding.id,
            ticker=holding.ticker,
            shares=holding.shares,
            purchase_price=holding.purchase_price,
            current_price=current_price,
            current_value=current_value,
            gain_loss=gain_loss,
            gain_loss_percent=gain_loss_percent,
            created_at=holding.created_at,
            updated_at=holding.updated_at,
        )
