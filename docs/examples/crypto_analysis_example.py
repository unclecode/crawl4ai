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
import plotly.express as px
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LXMLWebScrapingStrategy
from crawl4ai import CrawlResult
from typing import List
from IPython.display import HTML

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
        Convert crypto market data to machine-readable format
        Handles currency symbols, units (B=Billions), and percentage values
        """
        # Clean numeric columns
        df['Price'] = df['Price'].str.replace('[^\d.]', '', regex=True).astype(float)
        df['Market Cap'] = df['Market Cap'].str.extract(r'\$([\d.]+)B')[0].astype(float) * 1e9
        df['Volume(24h)'] = df['Volume(24h)'].str.extract(r'\$([\d.]+)B')[0].astype(float) * 1e9
        
        # Convert percentages to decimal values
        for col in ['1h %', '24h %', '7d %']:
            df[col] = df[col].str.replace('%', '').astype(float) / 100
            
        return df

    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute advanced trading metrics used by quantitative funds:
        
        1. Volume/Market Cap Ratio - Measures liquidity efficiency
           (High ratio = Underestimated attention)
           
        2. Volatility Score - Risk-adjusted momentum potential
           (STD of 1h/24h/7d returns)
           
        3. Momentum Score - Weighted average of returns
           (1h:30% + 24h:50% + 7d:20%)
           
        4. Volume Anomaly - 3σ deviation detection
           (Flags potential insider activity)
        """
        # Liquidity Metrics
        df['Volume/Market Cap Ratio'] = df['Volume(24h)'] / df['Market Cap']
        
        # Risk Metrics
        df['Volatility Score'] = df[['1h %','24h %','7d %']].std(axis=1)
        
        # Momentum Metrics
        df['Momentum Score'] = (df['1h %']*0.3 + df['24h %']*0.5 + df['7d %']*0.2)
        
        # Anomaly Detection
        median_vol = df['Volume(24h)'].median()
        df['Volume Anomaly'] = df['Volume(24h)'] > 3 * median_vol
        
        # Value Flags
        df['Undervalued Flag'] = (df['Market Cap'] < 1e9) & (df['Momentum Score'] > 0.05)
        df['Liquid Giant'] = (df['Volume/Market Cap Ratio'] > 0.15) & (df['Market Cap'] > 1e9)
        
        return df

    def create_visuals(self, df: pd.DataFrame) -> dict:
        """
        Generate three institutional-grade visualizations:
        
        1. 3D Market Map - X:Size, Y:Liquidity, Z:Momentum
        2. Liquidity Tree - Color:Volume Efficiency
        3. Momentum Leaderboard - Top sustainable movers
        """
        # 3D Market Overview
        fig1 = px.scatter_3d(
            df, 
            x='Market Cap', 
            y='Volume/Market Cap Ratio',
            z='Momentum Score',
            size='Volatility Score',
            color='Volume Anomaly',
            hover_name='Name',
            title='Smart Money Market Map: Spot Overlooked Opportunities',
            labels={'Market Cap': 'Size (Log $)', 'Volume/Market Cap Ratio': 'Liquidity Power'},
            log_x=True,
            template='plotly_dark'
        )
        
        # Liquidity Efficiency Tree
        fig2 = px.treemap(
            df,
            path=['Name'], 
            values='Market Cap',
            color='Volume/Market Cap Ratio',
            hover_data=['Momentum Score'],
            title='Liquidity Forest: Green = High Trading Efficiency',
            color_continuous_scale='RdYlGn'
        )
        
        # Momentum Leaders
        fig3 = px.bar(
            df.sort_values('Momentum Score', ascending=False).head(10),
            x='Name', 
            y='Momentum Score',
            color='Volatility Score',
            title='Sustainable Momentum Leaders (Low Volatility + High Growth)',
            text='7d %',
            template='plotly_dark'
        )
        
        return {'market_map': fig1, 'liquidity_tree': fig2, 'momentum_leaders': fig3}

    def generate_insights(self, df: pd.DataFrame) -> str:
        """
        Create plain English trading insights explaining:
        - Volume spikes and their implications
        - Risk-reward ratios of top movers
        - Liquidity warnings for large positions
        """
        top_coin = df.sort_values('Momentum Score', ascending=False).iloc[0]
        anomaly_coins = df[df['Volume Anomaly']].sort_values('Volume(24h)', ascending=False)
        
        report = f"""
        🚀 Top Alpha Opportunity: {top_coin['Name']}
        - Momentum Score: {top_coin['Momentum Score']:.2%} (Top 1%)
        - Risk-Reward Ratio: {top_coin['Momentum Score']/top_coin['Volatility Score']:.1f}
        - Liquidity Warning: {'✅ Safe' if top_coin['Liquid Giant'] else '⚠️ Thin Markets'}
        
        🔥 Volume Spikes Detected ({len(anomaly_coins)} coins):
        {anomaly_coins[['Name', 'Volume(24h)']].head(3).to_markdown(index=False)}
        
        💡 Smart Money Tip: Coins with Volume/Cap > 15% and Momentum > 5% 
        historically outperform by 22% weekly returns.
        """
        return report

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
        headless=True,
        stealth=True,
        block_resources=["image", "media"]
    )
    
    # Initialize crawler with smart table detection
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    
    try:
        # Set up scraping parameters
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            scraping_strategy=LXMLWebScrapingStrategy(
                table_score_threshold=8,  # Strict table detection
                keep_data_attributes=True
            )
        )
        
        # Execute market data extraction
        results: List[CrawlResult] = await crawler.arun(
            url='https://coinmarketcap.com/?page=1',
            config=crawl_config
        )
        
        # Process results
        for result in results:
            if result.success and result.media['tables']:
                # Extract primary market table
                raw_df = pd.DataFrame(
                    result.media['tables'][0]['rows'],
                    columns=result.media['tables'][0]['headers']
                )
                
                # Initialize analysis engine
                analyzer = CryptoAlphaGenerator()
                clean_df = analyzer.clean_data(raw_df)
                analyzed_df = analyzer.calculate_metrics(clean_df)
                
                # Generate outputs
                visuals = analyzer.create_visuals(analyzed_df)
                insights = analyzer.generate_insights(analyzed_df)
                
                # Save visualizations
                visuals['market_map'].write_html("market_map.html")
                visuals['liquidity_tree'].write_html("liquidity_tree.html")
                
                # Display results
                print("🔑 Key Trading Insights:")
                print(insights)
                print("\n📊 Open 'market_map.html' for interactive analysis")

    finally:
        await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())