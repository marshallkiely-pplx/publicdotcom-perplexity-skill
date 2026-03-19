import argparse
import sys

from config import get_api_secret, get_account_id, create_client


def get_portfolio(account_id=None):
    secret = get_api_secret()
    account_id = account_id or get_account_id()

    if not secret:
        print("Error: PUBLIC_COM_SECRET is not set.")
        sys.exit(1)

    if not account_id:
        print("Error: No account ID provided. Either pass --account-id or set PUBLIC_COM_ACCOUNT_ID.")
        sys.exit(1)

    try:
        client = create_client(secret, account_id)

        portfolio = client.get_portfolio()

        # Account Info
        print(f"## PORTFOLIO - Account: {portfolio.account_id} ({portfolio.account_type.value})")

        # Portfolio Summary as markdown table
        bp = portfolio.buying_power
        total_equity = sum(e.value for e in portfolio.equity)

        # Compute total cost basis and gain/loss from positions
        total_cost_basis = 0
        total_gain_loss = 0
        total_day_change = 0
        has_cost_basis = False
        has_day_change = False

        if portfolio.positions:
            for pos in portfolio.positions:
                if pos.cost_basis:
                    has_cost_basis = True
                    total_cost_basis += pos.cost_basis.total_cost
                    total_gain_loss += pos.cost_basis.gain_value
                if pos.position_daily_gain:
                    has_day_change = True
                    total_day_change += pos.position_daily_gain.gain_value

        print()
        print("| Metric | Value |")
        print("| --- | --- |")
        print(f"| Total Equity | ${total_equity:,.2f} |")
        if has_cost_basis:
            print(f"| Total Cost Basis | ${total_cost_basis:,.2f} |")
            gain_sign = "+" if total_gain_loss >= 0 else ""
            print(f"| Reported Gain/Loss | {gain_sign}${total_gain_loss:,.2f} |")
        if has_day_change:
            day_sign = "+" if total_day_change >= 0 else ""
            print(f"| Today's Change | {day_sign}${total_day_change:,.2f} |")
        print(f"| Buying Power | ${bp.buying_power:,.2f} |")

        # Equity Breakdown
        print()
        print("### Equity Breakdown")
        print()
        print("| Asset Type | Value | % of Portfolio |")
        print("| --- | --- | --- |")
        for eq in portfolio.equity:
            asset_type = eq.type.value.replace("_", " ").title()
            print(f"| {asset_type} | ${eq.value:,.2f} | {eq.percentage_of_portfolio:.2f}% |")

        # Group positions by type
        if portfolio.positions:
            equities = [p for p in portfolio.positions if p.instrument.type.value == "EQUITY"]
            options = [p for p in portfolio.positions if p.instrument.type.value == "OPTION"]
            crypto = [p for p in portfolio.positions if p.instrument.type.value == "CRYPTO"]

            def print_positions_table(positions, title):
                print()
                print(f"### {title}")
                print()
                print("| Ticker | Name | Value | Portfolio Weight | Day Change % | Gain/Loss |")
                print("| --- | --- | --- | --- | --- | --- |")
                for pos in positions:
                    inst = pos.instrument
                    value = f"${pos.current_value:,.2f}"
                    weight = f"{pos.percent_of_portfolio:.1f}%"

                    if pos.position_daily_gain:
                        dg = pos.position_daily_gain
                        day_sign = "+" if dg.gain_percentage >= 0 else ""
                        day_change = f"{day_sign}{dg.gain_percentage:.2f}%"
                    else:
                        day_change = "\u2014"

                    if pos.cost_basis:
                        cb = pos.cost_basis
                        gain_sign = "+" if cb.gain_percentage >= 0 else ""
                        gain_loss = f"{gain_sign}{cb.gain_percentage:,.0f}%"
                    else:
                        gain_loss = "\u2014"

                    print(f"| {inst.symbol} | {inst.name} | {value} | {weight} | {day_change} | {gain_loss} |")

            if equities:
                print_positions_table(equities, "Holdings by Weight")

            if options:
                print_positions_table(options, "Options Positions")

            if crypto:
                print_positions_table(crypto, "Crypto Positions")

        client.close()
    except Exception as e:
        print(f"Error fetching portfolio: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--account-id", required=False, help="Your Public.com account ID (uses PUBLIC_COM_ACCOUNT_ID env var if not provided)")
    args = parser.parse_args()
    get_portfolio(args.account_id)
