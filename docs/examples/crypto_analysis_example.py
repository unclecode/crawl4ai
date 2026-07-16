"""
Crawl4AI Crypto Trading Analysis Demo
Author: Unclecode
Date: 2024-03-15

This script demonstrates advanced crypto market analysis using:
1. Web scraping of real-time CoinMarketCap data
2. Smart table extraction with layout detection
3. Hedge fund-grade financial metrics
4. Interactive visualizations for trading signals

Key Features:
- Volume Anomaly Detection: Finds unusual trading activity
- Liquidity Power Score: Identifies easily tradable assets
- Volatility-Weighted Momentum: Surface sustainable trends
- Smart Money Signals: Algorithmic buy/hold recommendations
"""

import asyncio
import pandas as pd
import numpy as np
import re
import plotly.express as px
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LXMLWebScrapingStrategy,
)
from crawl4ai import CrawlResult
from typing import List

__current_dir__ = __file__.rsplit("/", 1)[0]

class CryptoAlphaGenerator:
    """
    Advanced crypto analysis engine that transforms raw web data into:
    - Volume anomaly flags
    - Liquidity scores
    - Momentum-risk ratios
    - Machine learning-inspired trading signals

    Methods:
    analyze_tables(): Process raw tables into trading insights
    create_visuals(): Generate institutional-grade visualizations
    generate_insights(): Create plain English trading recommendations
    """

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert crypto market data to machine-readable format.
        Handles currency symbols, units (B=Billions), and percentage values.
        """
        # Make a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Clean Price column (handle currency symbols)
        df["Price"] = df["Price"].astype(str).str.replace("[^\d.]", "", regex=True).astype(float)
        
        # Handle Market Cap and Volume, considering both Billions and Trillions
        def convert_large_numbers(value):
            if pd.isna(value):
                return float('nan')
            value = str(value)
            multiplier = 1
            if 'B' in value:
                multiplier = 1e9
            elif 'T' in value:
                multiplier = 1e12
            # Handle cases where the value might already be numeric
            cleaned_value = re.sub(r"[^\d.]", "", value)
            return float(cleaned_value) * multiplier if cleaned_value else float('nan')
        
        df["Market Cap"] = df["Market Cap"].apply(convert_large_numbers)
        df["Volume(24h)"] = df["Volume(24h)"].apply(convert_large_numbers)
        
        # Convert percentages to decimal values
        for col in ["1h %", "24h %", "7d %"]:
            if col in df.columns:
                # First ensure it's string, then clean
                df[col] = (
                    df[col].astype(str)
                    .str.replace("%", "")
                    .str.replace(",", ".")
                    .replace("nan", np.nan)
                )
                df[col] = pd.to_numeric(df[col], errors='coerce') / 100
        
        return df

    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute advanced trading metrics used by quantitative funds:

        1. Volume/Market Cap Ratio - Measures liquidity efficiency
           (High ratio = Underestimated attention, and small-cap = higher growth potential)

        2. Volatility Score - Risk-adjusted momentum potential - Shows how stable is the trend
           (STD of 1h/24h/7d returns)

        3. Momentum Score - Weighted average of returns - Shows how strong is the trend
           (1h:30% + 24h:50% + 7d:20%)

        4. Volume Anomaly - 3σ deviation detection
           (Flags potential insider activity) - Unusual trading activity – Flags coins with volume spikes (potential insider buying or news).
        """
        # Liquidity Metrics
        df["Volume/Market Cap Ratio"] = df["Volume(24h)"] / df["Market Cap"]

        # Risk Metrics
        df["Volatility Score"] = df[["1h %", "24h %", "7d %"]].std(axis=1)

        # Momentum Metrics
        df["Momentum Score"] = df["1h %"] * 0.3 + df["24h %"] * 0.5 + df["7d %"] * 0.2

        # Anomaly Detection
        median_vol = df["Volume(24h)"].median()
        df["Volume Anomaly"] = df["Volume(24h)"] > 3 * median_vol

        # Value Flags
        # Undervalued Flag - Low market cap and high momentum
        # (High growth potential and low attention)
        df["Undervalued Flag"] = (df["Market Cap"] < 1e9) & (
            df["Momentum Score"] > 0.05
        )
        # Liquid Giant Flag - High volume/market cap ratio and large market cap
        # (High liquidity and large market cap = institutional interest)
        df["Liquid Giant"] = (df["Volume/Market Cap Ratio"] > 0.15) & (
            df["Market Cap"] > 1e9
        )

        return df

    def generate_insights_simple(self, df: pd.DataFrame) -> str:
        """
        Generates an ultra-actionable crypto trading report with:
        - Risk-tiered opportunities (High/Medium/Low)
        - Concrete examples for each trade type
        - Entry/exit strategies spelled out
        - Visual cues for quick scanning
        """
        report = [
            "🚀 **CRYPTO TRADING CHEAT SHEET** 🚀",
            "*Based on quantitative signals + hedge fund tactics*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        # 1. HIGH-RISK: Undervalued Small-Caps (Momentum Plays)
        high_risk = df[df["Undervalued Flag"]].sort_values("Momentum Score", ascending=False)
        if not high_risk.empty:
            example_coin = high_risk.iloc[0]
            report.extend([
                "\n🔥 **HIGH-RISK: Rocket Fuel Small-Caps**",
                f"*Example Trade:* {example_coin['Name']} (Price: ${example_coin['Price']:.6f})",
                "📊 *Why?* Tiny market cap (<$1B) but STRONG momentum (+{:.0f}% last week)".format(example_coin['7d %']*100),
                "🎯 *Strategy:*",
                "1. Wait for 5-10% dip from recent high (${:.6f} → Buy under ${:.6f})".format(
                    example_coin['Price'] / (1 - example_coin['24h %']),  # Approx recent high
                    example_coin['Price'] * 0.95
                ),
                "2. Set stop-loss at -10% (${:.6f})".format(example_coin['Price'] * 0.90),
                "3. Take profit at +20% (${:.6f})".format(example_coin['Price'] * 1.20),
                "⚠️ *Risk Warning:* These can drop 30% fast! Never bet more than 5% of your portfolio.",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ])

        # 2. MEDIUM-RISK: Liquid Giants (Swing Trades)
        medium_risk = df[df["Liquid Giant"]].sort_values("Volume/Market Cap Ratio", ascending=False)
        if not medium_risk.empty:
            example_coin = medium_risk.iloc[0]
            report.extend([
                "\n💎 **MEDIUM-RISK: Liquid Giants (Safe Swing Trades)**",
                f"*Example Trade:* {example_coin['Name']} (Market Cap: ${example_coin['Market Cap']/1e9:.1f}B)",
                "📊 *Why?* Huge volume (${:.1f}M/day) makes it easy to enter/exit".format(example_coin['Volume(24h)']/1e6),
                "🎯 *Strategy:*",
                "1. Buy when 24h volume > 15% of market cap (Current: {:.0f}%)".format(example_coin['Volume/Market Cap Ratio']*100),
                "2. Hold 1-4 weeks (Big coins trend longer)",
                "3. Exit when momentum drops below 5% (Current: {:.0f}%)".format(example_coin['Momentum Score']*100),
                "📉 *Pro Tip:* Watch Bitcoin's trend - if BTC drops 5%, these usually follow.",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ])

        # 3. LOW-RISK: Stable Momentum (DCA Targets)
        low_risk = df[
            (df["Momentum Score"] > 0.05) & 
            (df["Volatility Score"] < 0.03)
        ].sort_values("Market Cap", ascending=False)
        if not low_risk.empty:
            example_coin = low_risk.iloc[0]
            report.extend([
                "\n🛡️ **LOW-RISK: Steady Climbers (DCA & Forget)**",
                f"*Example Trade:* {example_coin['Name']} (Volatility: {example_coin['Volatility Score']:.2f}/5)",
                "📊 *Why?* Rises steadily (+{:.0f}%/week) with LOW drama".format(example_coin['7d %']*100),
                "🎯 *Strategy:*",
                "1. Buy small amounts every Tuesday/Friday (DCA)",
                "2. Hold for 3+ months (Compound gains work best here)",
                "3. Sell 10% at every +25% milestone",
                "💰 *Best For:* Long-term investors who hate sleepless nights",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ])

        # Volume Spike Alerts
        anomalies = df[df["Volume Anomaly"]].sort_values("Volume(24h)", ascending=False)
        if not anomalies.empty:
            example_coin = anomalies.iloc[0]
            report.extend([
                "\n🚨 **Volume Spike Alert (Possible News/Whale Action)**",
                f"*Coin:* {example_coin['Name']} (Volume: ${example_coin['Volume(24h)']/1e6:.1f}M, usual: ${example_coin['Volume(24h)']/3/1e6:.1f}M)",
                "🔍 *Check:* Twitter/CoinGecko for news before trading",
                "⚡ *If no news:* Could be insider buying - watch price action:",
                "- Break above today's high → Buy with tight stop-loss",
                "- Fade back down → Avoid (may be a fakeout)"
            ])

        # Pro Tip Footer
        report.append("\n✨ *Pro Tip:* Bookmark this report & check back in 24h to see if signals held up.")

        return "\n".join(report)

    def generate_insights(self, df: pd.DataFrame) -> str:
        """
        Generates a tactical trading report with:
        - Top 3 trades per risk level (High/Medium/Low)
        - Auto-calculated entry/exit prices
        - BTC chart toggle tip
        """
        # Filter top candidates for each risk level
        high_risk = (
            df[df["Undervalued Flag"]]
            .sort_values("Momentum Score", ascending=False)
            .head(3)
        )
        medium_risk = (
            df[df["Liquid Giant"]]
            .sort_values("Volume/Market Cap Ratio", ascending=False)
            .head(3)
        )
        low_risk = (
            df[(df["Momentum Score"] > 0.05) & (df["Volatility Score"] < 0.03)]
            .sort_values("Momentum Score", ascending=False)
            .head(3)
        )

        report = ["# 🎯 Crypto Trading Tactical Report (Top 3 Per Risk Tier)"]
        
        # 1. High-Risk Trades (Small-Cap Momentum)
        if not high_risk.empty:
            report.append("\n## 🔥 HIGH RISK: Small-Cap Rockets (5-50% Potential)")
            for i, coin in high_risk.iterrows():
                current_price = coin["Price"]
                entry = current_price * 0.95  # -5% dip
                stop_loss = current_price * 0.90  # -10%
                take_profit = current_price * 1.20  # +20%
                
                report.append(
                    f"\n### {coin['Name']} (Momentum: {coin['Momentum Score']:.1%})"
                    f"\n- **Current Price:** ${current_price:.4f}"
                    f"\n- **Entry:** < ${entry:.4f} (Wait for pullback)"
                    f"\n- **Stop-Loss:** ${stop_loss:.4f} (-10%)"
                    f"\n- **Target:** ${take_profit:.4f} (+20%)"
                    f"\n- **Risk/Reward:** 1:2"
                    f"\n- **Watch:** Volume spikes above {coin['Volume(24h)']/1e6:.1f}M"
                )

        # 2. Medium-Risk Trades (Liquid Giants)
        if not medium_risk.empty:
            report.append("\n## 💎 MEDIUM RISK: Liquid Swing Trades (10-30% Potential)")
            for i, coin in medium_risk.iterrows():
                current_price = coin["Price"]
                entry = current_price * 0.98  # -2% dip
                stop_loss = current_price * 0.94  # -6%
                take_profit = current_price * 1.15  # +15%
                
                report.append(
                    f"\n### {coin['Name']} (Liquidity Score: {coin['Volume/Market Cap Ratio']:.1%})"
                    f"\n- **Current Price:** ${current_price:.2f}"
                    f"\n- **Entry:** < ${entry:.2f} (Buy slight dips)"
                    f"\n- **Stop-Loss:** ${stop_loss:.2f} (-6%)"
                    f"\n- **Target:** ${take_profit:.2f} (+15%)"
                    f"\n- **Hold Time:** 1-3 weeks"
                    f"\n- **Key Metric:** Volume/Cap > 15%"
                )

        # 3. Low-Risk Trades (Stable Momentum)
        if not low_risk.empty:
            report.append("\n## 🛡️ LOW RISK: Steady Gainers (5-15% Potential)")
            for i, coin in low_risk.iterrows():
                current_price = coin["Price"]
                entry = current_price * 0.99  # -1% dip
                stop_loss = current_price * 0.97  # -3%
                take_profit = current_price * 1.10  # +10%
                
                report.append(
                    f"\n### {coin['Name']} (Stability Score: {1/coin['Volatility Score']:.1f}x)"
                    f"\n- **Current Price:** ${current_price:.2f}"
                    f"\n- **Entry:** < ${entry:.2f} (Safe zone)"
                    f"\n- **Stop-Loss:** ${stop_loss:.2f} (-3%)"
                    f"\n- **Target:** ${take_profit:.2f} (+10%)"
                    f"\n- **DCA Suggestion:** 3 buys over 72 hours"
                )

        # Volume Anomaly Alert
        anomalies = df[df["Volume Anomaly"]].sort_values("Volume(24h)", ascending=False).head(2)
        if not anomalies.empty:
            report.append("\n⚠️ **Volume Spike Alerts**")
            for i, coin in anomalies.iterrows():
                report.append(
                    f"- {coin['Name']}: Volume {coin['Volume(24h)']/1e6:.1f}M "
                    f"(3x normal) | Price moved: {coin['24h %']:.1%}"
                )

        # Pro Tip
        report.append(
            "\n📊 **Chart Hack:** Hide BTC in visuals:\n"
            "```python\n"
            "# For 3D Map:\n"
            "fig.update_traces(visible=False, selector={'name':'Bitcoin'})\n"
            "# For Treemap:\n"
            "df = df[df['Name'] != 'Bitcoin']\n"
            "```"
        )

        return "\n".join(report)

    def create_visuals(self, df: pd.DataFrame) -> dict:
        """Enhanced visuals with BTC toggle support"""
        # 3D Market Map (with BTC toggle hint)
        fig1 = px.scatter_3d(
            df,
            x="Market Cap",
            y="Volume/Market Cap Ratio",
            z="Momentum Score",
            color="Name",  # Color by name to allow toggling
            hover_name="Name",
            title="Market Map (Toggle BTC in legend to focus on alts)",
            log_x=True
        )
        fig1.update_traces(
            marker=dict(size=df["Volatility Score"]*100 + 5)  # Dynamic sizing
        )
        
        # Liquidity Tree (exclude BTC if too dominant)
        if df[df["Name"] == "BitcoinBTC"]["Market Cap"].values[0] > df["Market Cap"].median() * 10:
            df = df[df["Name"] != "BitcoinBTC"]
        
        fig2 = px.treemap(
            df,
            path=["Name"],
            values="Market Cap",
            color="Volume/Market Cap Ratio",
            title="Liquidity Tree (BTC auto-removed if dominant)"
        )
        
        return {"market_map": fig1, "liquidity_tree": fig2}

async def main():
    """
    Main execution flow:
    1. Configure headless browser for scraping
    2. Extract live crypto market data
    3. Clean and analyze using hedge fund models
    4. Generate visualizations and insights
    5. Output professional trading report
    """
    # Configure browser with anti-detection features
    browser_config = BrowserConfig(
        headless=False,
    )

    # Initialize crawler with smart table detection
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        # Set up scraping parameters
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            table_score_threshold=8,  # Strict table detection
            keep_data_attributes=True,
            scraping_strategy=LXMLWebScrapingStrategy(),
            scan_full_page=True,
            scroll_delay=0.2,
        )

        # Execute market data extraction
        results: List[CrawlResult] = await crawler.arun(
            url="https://coinmarketcap.com/?page=1", config=crawl_config
        )

        # Process results
        raw_df = pd.DataFrame()
        for result in results:
            # Use the new tables field, falling back to media["tables"] for backward compatibility
            tables = result.tables if hasattr(result, "tables") and result.tables else result.media.get("tables", [])
            if result.success and tables:
                # Extract primary market table
                # DataFrame
                raw_df = pd.DataFrame(
                    tables[0]["rows"],
                    columns=tables[0]["headers"],
                )
                break


        # This is for debugging only
        # ////// Remove this in production from here..
        # Save raw data for debugging
        raw_df.to_csv(f"{__current_dir__}/tmp/raw_crypto_data.csv", index=False)
        print("🔍 Raw data saved to 'raw_crypto_data.csv'")

        # Read from file for debugging
        raw_df = pd.read_csv(f"{__current_dir__}/tmp/raw_crypto_data.csv")
        # ////// ..to here

        # Select top 20
        raw_df = raw_df.head(50)
        # Remove "Buy" from name
        raw_df["Name"] = raw_df["Name"].str.replace("Buy", "")

        # Initialize analysis engine
        analyzer = CryptoAlphaGenerator()
        clean_df = analyzer.clean_data(raw_df)
        analyzed_df = analyzer.calculate_metrics(clean_df)

        # Generate outputs
        visuals = analyzer.create_visuals(analyzed_df)
        insights = analyzer.generate_insights(analyzed_df)

        # Save visualizations
        visuals["market_map"].write_html(f"{__current_dir__}/tmp/market_map.html")
        visuals["liquidity_tree"].write_html(f"{__current_dir__}/tmp/liquidity_tree.html")

        # Display results
        print("🔑 Key Trading Insights:")
        print(insights)
        print("\n📊 Open 'market_map.html' for interactive analysis")
        print("\n📊 Open 'liquidity_tree.html' for interactive analysis")

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
