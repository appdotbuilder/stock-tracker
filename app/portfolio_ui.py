from decimal import Decimal
from nicegui import ui
from app.portfolio_service import PortfolioService


def create():
    """Create the portfolio tracking UI"""

    @ui.page("/")
    def portfolio_page():
        # Get or create default user
        user = PortfolioService.get_or_create_default_user()
        if user.id is None:
            ui.notify("Error: Unable to load user data", type="negative")
            return

        user_id = user.id

        # Apply modern theme
        ui.colors(
            primary="#2563eb",
            secondary="#64748b",
            accent="#10b981",
            positive="#10b981",
            negative="#ef4444",
            warning="#f59e0b",
            info="#3b82f6",
        )

        # Page header
        with ui.row().classes("w-full bg-white shadow-sm p-4 mb-6"):
            ui.label("📈 Stock Portfolio Tracker").classes("text-3xl font-bold text-gray-800")

        # Portfolio summary card
        with ui.card().classes("w-full p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500 mb-6"):
            summary_container = ui.column().classes("w-full")

        # Holdings table
        holdings_container = ui.column().classes("w-full")

        # Add holding form
        with ui.card().classes("w-full p-6 bg-white shadow-lg rounded-lg"):
            ui.label("Add New Stock Holding").classes("text-xl font-semibold text-gray-800 mb-4")

            with ui.row().classes("w-full gap-4"):
                ticker_input = (
                    ui.input(label="Stock Ticker", placeholder="e.g., AAPL, GOOGL, MSFT")
                    .classes("flex-1")
                    .props("outlined")
                )

                shares_input = (
                    ui.number(label="Number of Shares", value=0, min=0.01, step=0.01, format="%.2f")
                    .classes("flex-1")
                    .props("outlined")
                )

                price_input = (
                    ui.number(label="Purchase Price ($)", value=0, min=0.01, step=0.01, format="%.2f")
                    .classes("flex-1")
                    .props("outlined")
                )

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button(
                    "Add Holding", on_click=lambda: add_holding(user_id, ticker_input, shares_input, price_input)
                ).classes("bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg")

                ui.button("Refresh Portfolio", on_click=lambda: refresh_portfolio(user_id)).classes(
                    "bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg"
                ).props("outline")

        def refresh_portfolio(user_id: int):
            """Refresh the entire portfolio display"""
            refresh_summary(user_id)
            refresh_holdings(user_id)

        def refresh_summary(user_id: int):
            """Refresh the portfolio summary display"""
            summary_container.clear()

            with summary_container:
                ui.label("Portfolio Summary").classes("text-2xl font-bold text-gray-800 mb-4")

                try:
                    summary = PortfolioService.get_portfolio_summary(user_id)

                    with ui.row().classes("w-full gap-6"):
                        # Current Value
                        with ui.column().classes("text-center"):
                            ui.label("Current Value").classes("text-sm text-gray-600 uppercase tracking-wider")
                            ui.label(f"${summary.total_current_value:,.2f}").classes("text-3xl font-bold text-gray-800")

                        # Purchase Value
                        with ui.column().classes("text-center"):
                            ui.label("Purchase Value").classes("text-sm text-gray-600 uppercase tracking-wider")
                            ui.label(f"${summary.total_purchase_value:,.2f}").classes(
                                "text-3xl font-bold text-gray-800"
                            )

                        # Gain/Loss
                        with ui.column().classes("text-center"):
                            ui.label("Gain/Loss").classes("text-sm text-gray-600 uppercase tracking-wider")
                            gain_loss_color = "text-green-600" if summary.total_gain_loss >= 0 else "text-red-600"
                            sign = "+" if summary.total_gain_loss >= 0 else ""
                            ui.label(f"{sign}${summary.total_gain_loss:,.2f}").classes(
                                f"text-3xl font-bold {gain_loss_color}"
                            )

                        # Percentage
                        with ui.column().classes("text-center"):
                            ui.label("% Change").classes("text-sm text-gray-600 uppercase tracking-wider")
                            percent_color = "text-green-600" if summary.total_gain_loss_percent >= 0 else "text-red-600"
                            sign = "+" if summary.total_gain_loss_percent >= 0 else ""
                            ui.label(f"{sign}{summary.total_gain_loss_percent:.2f}%").classes(
                                f"text-3xl font-bold {percent_color}"
                            )

                        # Holdings Count
                        with ui.column().classes("text-center"):
                            ui.label("Holdings").classes("text-sm text-gray-600 uppercase tracking-wider")
                            ui.label(str(summary.holdings_count)).classes("text-3xl font-bold text-gray-800")

                except Exception as e:
                    ui.label(f"Error loading portfolio summary: {str(e)}").classes("text-red-600")

        def refresh_holdings(user_id: int):
            """Refresh the holdings table"""
            holdings_container.clear()

            with holdings_container:
                ui.label("Stock Holdings").classes("text-2xl font-bold text-gray-800 mb-4")

                try:
                    holdings = PortfolioService.get_holdings_with_prices(user_id)

                    if not holdings:
                        ui.label("No holdings found. Add your first stock above!").classes(
                            "text-gray-500 text-center p-8"
                        )
                        return

                    # Create table data
                    columns = [
                        {"name": "ticker", "label": "Ticker", "field": "ticker", "align": "left"},
                        {"name": "shares", "label": "Shares", "field": "shares", "align": "right"},
                        {
                            "name": "purchase_price",
                            "label": "Purchase Price",
                            "field": "purchase_price",
                            "align": "right",
                        },
                        {"name": "current_price", "label": "Current Price", "field": "current_price", "align": "right"},
                        {"name": "current_value", "label": "Current Value", "field": "current_value", "align": "right"},
                        {"name": "gain_loss", "label": "Gain/Loss", "field": "gain_loss", "align": "right"},
                        {
                            "name": "gain_loss_percent",
                            "label": "% Change",
                            "field": "gain_loss_percent",
                            "align": "right",
                        },
                        {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
                    ]

                    rows = []
                    for holding in holdings:
                        gain_loss_sign = "+" if holding.gain_loss >= 0 else ""
                        percent_sign = "+" if holding.gain_loss_percent >= 0 else ""

                        rows.append(
                            {
                                "ticker": holding.ticker,
                                "shares": f"{holding.shares:.2f}",
                                "purchase_price": f"${holding.purchase_price:.2f}",
                                "current_price": f"${holding.current_price:.2f}",
                                "current_value": f"${holding.current_value:.2f}",
                                "gain_loss": f"{gain_loss_sign}${holding.gain_loss:.2f}",
                                "gain_loss_percent": f"{percent_sign}{holding.gain_loss_percent:.2f}%",
                                "actions": holding.id,
                            }
                        )

                    table = ui.table(columns=columns, rows=rows).classes("w-full")
                    table.add_slot(
                        "body-cell-actions",
                        """
                        <q-td :props="props">
                            <q-btn 
                                flat 
                                round 
                                color="negative" 
                                icon="delete" 
                                @click="$parent.$emit('delete-holding', props.row.actions)"
                            />
                        </q-td>
                    """,
                    )

                    # Handle delete holding
                    def delete_holding(e):
                        holding_id = e.args
                        if PortfolioService.delete_holding(holding_id):
                            ui.notify("Holding deleted successfully", type="positive")
                            refresh_portfolio(user_id)
                        else:
                            ui.notify("Error deleting holding", type="negative")

                    table.on("delete-holding", delete_holding)

                except Exception as e:
                    ui.label(f"Error loading holdings: {str(e)}").classes("text-red-600")

        async def add_holding(user_id: int, ticker_input, shares_input, price_input):
            """Add a new stock holding"""
            ticker = ticker_input.value.strip().upper()
            shares = shares_input.value
            price = price_input.value

            # Validation
            if not ticker:
                ui.notify("Please enter a stock ticker", type="negative")
                return

            if not shares or shares <= 0:
                ui.notify("Please enter a valid number of shares", type="negative")
                return

            if not price or price <= 0:
                ui.notify("Please enter a valid purchase price", type="negative")
                return

            # Show loading notification
            ui.notify("Adding holding and fetching current price...", type="info")

            try:
                # Convert to Decimal for precise calculations
                shares_decimal = Decimal(str(shares))
                price_decimal = Decimal(str(price))

                # Add the holding
                holding = PortfolioService.add_holding(user_id, ticker, shares_decimal, price_decimal)

                if holding:
                    ui.notify(f"Successfully added {shares} shares of {ticker}", type="positive")

                    # Clear form
                    ticker_input.set_value("")
                    shares_input.set_value(0)
                    price_input.set_value(0)

                    # Refresh portfolio
                    refresh_portfolio(user_id)
                else:
                    ui.notify(f"Invalid ticker symbol: {ticker}", type="negative")

            except Exception as e:
                ui.notify(f"Error adding holding: {str(e)}", type="negative")

        # Initial load
        refresh_portfolio(user_id)
