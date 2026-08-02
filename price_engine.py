import yfinance as yf
from nse_client import NSEClient
from utils import get_logger
import numpy as np

logger = get_logger(__name__)

class PriceEngine:
    def __init__(self):
        self.nse = NSEClient()
        
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        import pandas as pd
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(period).mean().iloc[-1]

    def fetch_market_cap(self, symbol: str) -> float:
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info
            return float(info.get("marketCap", 0.0))
        except Exception as e:
            logger.warning(f"Failed to fetch market cap for {symbol}: {e}")
            return 0.0

    def fetch_trade_levels(self, symbol: str, catalyst_score: int) -> dict:
        """
        Calculates Trade Levels using Market Data (Support, Resistance, ATR)
        Fetches Market Cap for company normalization.
        """
        levels = {
            "current_price": 0.0,
            "target_price": 0.0,
            "limit_price": 0.0,
            "exit_price": 0.0,
            "reliability": "No reliable trading levels available.",
            "market_cap": 0.0
        }
        
        # 1. Fetch Current Live Price via NSE API
        try:
            quote = self.nse.quote(symbol)
            if isinstance(quote, dict) and quote.get('tradeInfo'):
                levels["current_price"] = quote['tradeInfo'].get('lastPrice', 0.0)
                if levels["current_price"] == 0.0 and quote.get('metaData'):
                    levels["current_price"] = quote['metaData'].get('closePrice', 0.0)
        except Exception as e:
            logger.error(f"NSE API error for {symbol}: {e}")
            
        current_price = levels["current_price"]
            
        # 2. Fetch Historical Technical Data via YFinance for Indicators
        try:
            import pandas as pd
            # Note: yfinance for Indian stocks uses .NS suffix
            ticker = yf.Ticker(f"{symbol}.NS")
            
            # Fetch Market Cap
            info = ticker.info
            levels["market_cap"] = info.get("marketCap", 0.0)
            
            if current_price == 0.0:
                return levels
                
            df = ticker.history(period="3mo")
            
            # Strict Validation (Improvement 9)
            if df.empty or len(df) < 20:
                levels["reliability"] = "Unavailable (Insufficient History)"
                return levels
                
            if df['Close'].isnull().any() or df['High'].isnull().any() or df['Low'].isnull().any():
                levels["reliability"] = "Unavailable (Missing OHLC Data)"
                return levels
                
            # 3. Calculate Reliability Score
            reliability = "Medium"
            
            # Check ATR Volatility (e.g. if ATR > 10% of price, it's very volatile)
            atr = self._calculate_atr(df)
            
            if pd.isna(atr) or atr <= 0:
                levels["reliability"] = "Unavailable (Invalid ATR)"
                return levels
                
            avg_price = df['Close'].mean()
            atr_pct = (atr / avg_price) * 100 if avg_price > 0 else 0
            
            if atr_pct > 10:
                reliability = "Low (High Volatility)"
            elif atr_pct < 3:
                reliability = "High (Stable Trend)"
                
            # Volume check
            if 'Volume' not in df.columns or df['Volume'].mean() < 50000:
                reliability = "Low (Low Liquidity)"
                
            # Calculate Support (Recent Swing Low) and Resistance (Recent Swing High)
            support = df['Low'].min()
            resistance = df['High'].max()
            
            # Phase 6 Strict Validation
            if pd.isna(support) or pd.isna(resistance) or support >= resistance or pd.isna(atr):
                levels["reliability"] = "Unavailable (Invalid Support/Resistance/ATR)"
                return levels
                
            # Phase 7 Market Context
            fifty_two_week_high = info.get("fiftyTwoWeekHigh", 0.0)
            fifty_two_week_low = info.get("fiftyTwoWeekLow", 0.0)
            avg_volume = info.get("averageVolume", df['Volume'].mean())
            
            levels["distance_to_52w_high"] = ((fifty_two_week_high - current_price) / current_price) * 100 if current_price > 0 else 0
            levels["distance_to_52w_low"] = ((current_price - fifty_two_week_low) / fifty_two_week_low) * 100 if fifty_two_week_low > 0 else 0
            levels["trend"] = "Bullish" if current_price > df['Close'].mean() else "Bearish"
            
            # Dynamic Targeting based on Technicals
            levels["limit_price"] = current_price
            levels["target_price"] = resistance if resistance > current_price else current_price + (2 * atr)
            levels["exit_price"] = current_price - (1.5 * atr)
            levels["reliability"] = reliability
            
        except Exception as e:
            logger.error(f"YFinance error for {symbol}: {e}")
            
        return levels
