from decimal import Decimal
from typing import List, Optional
import yfinance as yf
from sqlmodel import select
from app.database import get_session
from app.models import StockHolding, User, HoldingWithCurrentPrice, PortfolioSummary


class PortfolioService:
    """Service for managing stock portfolio operations"""

    @staticmethod
    def get_stock_price(ticker: str) -> Optional[Decimal]:
        """Fetch current stock price from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker.upper())
            hist = stock.history(period="1d")
            if hist.empty:
                return None

            # Get the most recent closing price
            latest_price = hist["Close"].iloc[-1]
            return Decimal(str(round(latest_price, 2)))
        except Exception:
            return None

    @staticmethod
    def get_user_holdings(user_id: int) -> List[StockHolding]:
        """Get all holdings for a user"""
        with get_session() as session:
            statement = select(StockHolding).where(StockHolding.user_id == user_id)
            return list(session.exec(statement))

    @staticmethod
    def get_holdings_with_prices(user_id: int) -> List[HoldingWithCurrentPrice]:
        """Get all holdings with current market prices"""
        holdings = PortfolioService.get_user_holdings(user_id)
        holdings_with_prices = []

        for holding in holdings:
            current_price = PortfolioService.get_stock_price(holding.ticker)
            if current_price is not None:
                holdings_with_prices.append(HoldingWithCurrentPrice.from_holding(holding, current_price))

        return holdings_with_prices

    @staticmethod
    def get_portfolio_summary(user_id: int) -> PortfolioSummary:
        """Calculate portfolio summary with current values"""
        holdings_with_prices = PortfolioService.get_holdings_with_prices(user_id)

        total_current_value = Decimal("0")
        total_purchase_value = Decimal("0")

        for holding in holdings_with_prices:
            total_current_value += holding.current_value
            total_purchase_value += holding.shares * holding.purchase_price

        total_gain_loss = total_current_value - total_purchase_value
        total_gain_loss_percent = (
            (total_gain_loss / total_purchase_value * Decimal("100")) if total_purchase_value > 0 else Decimal("0")
        )

        return PortfolioSummary(
            total_current_value=total_current_value,
            total_purchase_value=total_purchase_value,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=total_gain_loss_percent,
            holdings_count=len(holdings_with_prices),
        )

    @staticmethod
    def add_holding(user_id: int, ticker: str, shares: Decimal, purchase_price: Decimal) -> Optional[StockHolding]:
        """Add a new stock holding"""
        # Validate ticker by checking if we can get price
        if PortfolioService.get_stock_price(ticker) is None:
            return None

        with get_session() as session:
            holding = StockHolding(ticker=ticker.upper(), shares=shares, purchase_price=purchase_price, user_id=user_id)
            session.add(holding)
            session.commit()
            session.refresh(holding)
            return holding

    @staticmethod
    def delete_holding(holding_id: int) -> bool:
        """Delete a stock holding"""
        with get_session() as session:
            holding = session.get(StockHolding, holding_id)
            if holding is None:
                return False
            session.delete(holding)
            session.commit()
            return True

    @staticmethod
    def get_or_create_default_user() -> User:
        """Get or create a default user for the application"""
        with get_session() as session:
            statement = select(User).where(User.email == "user@portfolio.com")
            user = session.exec(statement).first()

            if user is None:
                user = User(name="Portfolio User", email="user@portfolio.com")
                session.add(user)
                session.commit()
                session.refresh(user)

            return user
