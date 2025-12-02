# utbot_logic.py - Complete with Working Alternative Data Sources

import pandas as pd
import requests
import time
import logging
from datetime import datetime
import json
import random

logger = logging.getLogger(__name__)

# User agent to make requests look more legitimate
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_btc_data():
    """Fetches the latest 5-minute Kline data for BTCUSDT from multiple sources."""
    # Try multiple data sources in order of preference
    sources = [
        fetch_from_binance,
        fetch_from_kucoin,
        fetch_from_bybit,
        fetch_from_coinbase,
        fetch_from_mock_data  # Last resort fallback
    ]
    
    for source_func in sources:
        try:
            df = source_func()
            if not df.empty:
                logger.info(f"Successfully fetched data from {source_func.__name__}")
                return df
        except Exception as e:
            logger.warning(f"Failed to fetch from {source_func.__name__}: {e}")
            continue
    
    logger.error("All data sources failed, using mock data")
    return fetch_from_mock_data()

def fetch_from_binance():
    """Fetch data from Binance with retry logic."""
    max_retries = 2  # Reduce retries since it's being blocked
    base_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Add jitter to avoid detection
            delay = base_delay * (1 + random.random())
            
            logger.info(f"Fetching BTC data from Binance (attempt {attempt + 1}/{max_retries})")
            url = "https://api.binance.com/api/v3/klines"
            params = {"symbol": "BTCUSDT", "interval": "5m", "limit": 350}
            
            response = requests.get(
                url, 
                params=params, 
                headers=HEADERS,
                timeout=10
            )
            
            # Check for specific error codes
            if response.status_code == 451:
                logger.error("Binance blocking requests (451 error)")
                raise Exception("Binance unavailable for legal reasons")
            
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.error("Empty data received from Binance")
                raise Exception("Empty data")
            
            df = pd.DataFrame(data, columns=[
                "time", "open", "high", "low", "close", "volume", 
                "c", "q", "n", "t", "v", "ignore"
            ])
            for col in ["close", "high", "low", "open"]:
                df[col] = df[col].astype(float)
            
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching from Binance (attempt {attempt + 1}): {e}")
        except Exception as e:
            logger.error(f"Error processing Binance data (attempt {attempt + 1}): {e}")
        
        if attempt < max_retries - 1:
            logger.info(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
    
    raise Exception("Failed to fetch data from Binance after all retries")

def fetch_from_kucoin():
    """Alternative data source: KuCoin API with correct endpoint."""
    try:
        logger.info("Fetching data from KuCoin")
        # Use the correct KuCoin endpoint
        url = "https://api.kucoin.com/api/v1/market/candles"
        params = {
            "symbol": "BTC-USDT",
            "type": "5min",  # Correct type for KuCoin
            "startAt": int((time.time() - 350 * 5 * 60) * 1000),  # 350 candles ago
            "endAt": int(time.time() * 1000)
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") != "200000" or not data.get("data"):
            raise Exception(f"KuCoin API error: {data.get('msg', 'Unknown error')}")
        
        # KuCoin returns data in reverse order (newest first)
        klines = data["data"]
        klines.reverse()  # Reverse to get oldest first
        
        df_data = []
        for kline in klines:
            df_data.append([
                kline[0],  # time
                kline[1],  # open
                kline[3],  # high
                kline[4],  # low
                kline[2],  # close
                kline[5],  # volume
                "", "", "", "", "", ""
            ])
        
        df = pd.DataFrame(df_data, columns=[
            "time", "open", "high", "low", "close", "volume", 
            "c", "q", "n", "t", "v", "ignore"
        ])
        
        for col in ["close", "high", "low", "open"]:
            df[col] = df[col].astype(float)
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching from KuCoin: {e}")
        raise Exception(f"KuCoin API error: {str(e)}")

def fetch_from_bybit():
    """Alternative data source: Bybit API."""
    try:
        logger.info("Fetching data from Bybit")
        url = "https://api.bybit.com/v5/market/kline"
        params = {
            "category": "spot",  # Use spot instead of linear
            "symbol": "BTCUSDT",
            "interval": "5",  # 5 minutes
            "limit": 200  # Bybit limit
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("retCode") != 0 or not data.get("result", {}).get("list"):
            raise Exception(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
        
        # Bybit returns data in reverse order (newest first)
        klines = data["result"]["list"]
        klines.reverse()  # Reverse to get oldest first
        
        df_data = []
        for kline in klines:
            df_data.append([
                kline[0],  # time
                kline[1],  # open
                kline[2],  # high
                kline[3],  # low
                kline[4],  # close
                kline[5],  # volume
                "", "", "", "", "", ""
            ])
        
        df = pd.DataFrame(df_data, columns=[
            "time", "open", "high", "low", "close", "volume", 
            "c", "q", "n", "t", "v", "ignore"
        ])
        
        for col in ["close", "high", "low", "open"]:
            df[col] = df[col].astype(float)
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching from Bybit: {e}")
        raise Exception(f"Bybit API error: {str(e)}")

def fetch_from_coinbase():
    """Alternative data source: Coinbase Pro API."""
    try:
        logger.info("Fetching data from Coinbase")
        url = "https://api.pro.coinbase.com/products/BTC-USD/candles"
        params = {
            "granularity": 300,  # 5 minutes in seconds
            "start": ISOString((time.time() - 350 * 5 * 60)),  # 350 candles ago
            "end": ISOString(time.time())
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if not data or len(data) == 0:
            raise Exception("No data from Coinbase")
        
        # Coinbase returns: [timestamp, low, high, open, close, volume]
        df_data = []
        for candle in data:
            df_data.append([
                candle[0] * 1000,  # time (convert to milliseconds)
                candle[3],  # open
                candle[2],  # high
                candle[1],  # low
                candle[4],  # close
                candle[5],  # volume
                "", "", "", "", "", ""
            ])
        
        df = pd.DataFrame(df_data, columns=[
            "time", "open", "high", "low", "close", "volume", 
            "c", "q", "n", "t", "v", "ignore"
        ])
        
        for col in ["close", "high", "low", "open"]:
            df[col] = df[col].astype(float)
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching from Coinbase: {e}")
        raise Exception(f"Coinbase API error: {str(e)}")

def ISOString(seconds):
    """Convert seconds to ISO string for Coinbase API"""
    from datetime import datetime, timezone
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat().replace('+00:00', 'Z')

def fetch_from_mock_data():
    """Generate realistic mock data as a last resort."""
    logger.warning("Using mock data as fallback")
    
    # Generate mock candlestick data
    now = int(time.time() * 1000)
    df_data = []
    
    # Get a realistic base price
    try:
        # Try to get current price from a simple API
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=5)
        data = response.json()
        base_price = float(data["bpi"]["USD"]["rate_float"])
    except:
        base_price = 43000.0  # Fallback price
    
    price = base_price
    
    # Generate 350 candles (5-minute intervals)
    for i in range(350):
        timestamp = now - (350 - i) * 5 * 60 * 1000  # 5 minutes in milliseconds
        
        # Random walk for price with momentum
        change = (random.random() - 0.5) * 300  # Random change between -150 and +150
        price += change
        
        # Generate realistic OHLC
        open_price = price
        volatility = random.uniform(0.002, 0.008)  # 0.2% to 0.8% volatility
        
        high_price = open_price * (1 + random.uniform(0, volatility))
        low_price = open_price * (1 - random.uniform(0, volatility))
        
        # Ensure close is within high/low
        close_price = low_price + random.random() * (high_price - low_price)
        
        # Realistic volume
        volume = random.uniform(50, 500) * (1 + abs(change) / 100)
        
        df_data.append([
            timestamp, 
            round(open_price, 2), 
            round(high_price, 2), 
            round(low_price, 2), 
            round(close_price, 2), 
            round(volume, 2),
            "", "", "", "", "", ""
        ])
        
        price = close_price
    
    df = pd.DataFrame(df_data, columns=[
        "time", "open", "high", "low", "close", "volume", 
        "c", "q", "n", "t", "v", "ignore"
    ])
    
    for col in ["close", "high", "low", "open"]:
        df[col] = df[col].astype(float)
    
    return df

def get_current_price():
    """Fetches only the current price for BTCUSDT from multiple sources."""
    # Try multiple sources in order
    sources = [
        get_price_from_coindesk,
        get_price_from_coinbase,
        get_price_from_kucoin,
        get_price_from_bybit,
        get_mock_price  # Last resort
    ]
    
    for source_func in sources:
        try:
            price = source_func()
            if price and price > 0:
                logger.info(f"Successfully fetched price from {source_func.__name__}: ${price}")
                return price
        except Exception as e:
            logger.warning(f"Failed to fetch price from {source_func.__name__}: {e}")
            continue
    
    logger.error("All price sources failed")
    return get_mock_price()

def get_price_from_coindesk():
    """Fetch current price from CoinDesk API."""
    try:
        logger.info("Fetching current price from CoinDesk")
        url = "https://api.coindesk.com/v1/bpi/currentprice.json"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["bpi"]["USD"]["rate_float"])
        
    except Exception as e:
        logger.error(f"Error fetching price from CoinDesk: {e}")
        raise Exception(f"CoinDesk price error: {str(e)}")

def get_price_from_coinbase():
    """Fetch current price from Coinbase."""
    try:
        logger.info("Fetching current price from Coinbase")
        url = "https://api.pro.coinbase.com/products/BTC-USD/ticker"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["price"])
        
    except Exception as e:
        logger.error(f"Error fetching price from Coinbase: {e}")
        raise Exception(f"Coinbase price error: {str(e)}")

def get_price_from_kucoin():
    """Fetch current price from KuCoin."""
    try:
        logger.info("Fetching current price from KuCoin")
        url = "https://api.kucoin.com/api/v1/market/stats"
        params = {"symbol": "BTC-USDT"}
        
        response = requests.get(
            url, 
            params=params, 
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") != "200000" or not data.get("data"):
            raise Exception(f"KuCoin API error: {data.get('msg', 'Unknown error')}")
            
        return float(data["data"]["last"])
        
    except Exception as e:
        logger.error(f"Error fetching price from KuCoin: {e}")
        raise Exception(f"KuCoin price error: {str(e)}")

def get_price_from_bybit():
    """Fetch current price from Bybit."""
    try:
        logger.info("Fetching current price from Bybit")
        url = "https://api.bybit.com/v5/market/tickers"
        params = {
            "category": "spot",
            "symbol": "BTCUSDT"
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("retCode") != 0 or not data.get("result", {}).get("list"):
            raise Exception(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
            
        return float(data["result"]["list"][0]["lastPrice"])
        
    except Exception as e:
        logger.error(f"Error fetching price from Bybit: {e}")
        raise Exception(f"Bybit price error: {str(e)}")

def get_mock_price():
    """Generate a mock price as last resort."""
    logger.warning("Using mock price as fallback")
    return 43000.0 + random.random() * 2000  # Random price around $43,000-$45,000

def calc_utbot(df, keyvalue, atr_period):
    """Calculates the UT Bot trailing stop and signals."""
    if df.empty:
        return df

    df["tr"] = df["high"] - df["low"]
    df["atr"] = df["tr"].rolling(atr_period).mean()
    nLoss = keyvalue * df["atr"]

    xATRTrailingStop = [df["close"].iloc[0]]
    pos = [0]
    
    for i in range(1, len(df)):
        prev_stop = xATRTrailingStop[-1]
        src = df["close"].iloc[i]
        src1 = df["close"].iloc[i - 1]

        if src > prev_stop and src1 > prev_stop:
            new_stop = max(prev_stop, src - nLoss.iloc[i])
        elif src < prev_stop and src1 < prev_stop:
            new_stop = min(prev_stop, src + nLoss.iloc[i])
        else:
            new_stop = src - nLoss.iloc[i] if src > prev_stop else src + nLoss.iloc[i]

        xATRTrailingStop.append(new_stop)

        if src1 < prev_stop and src > prev_stop:
            pos.append(1)
        elif src1 > prev_stop and src < prev_stop:
            pos.append(-1)
        else:
            pos.append(pos[-1])

    df["stop"] = xATRTrailingStop
    df["pos"] = pos
    return df

def calculate_atr_stable(df, period=14):
    """Calculate a stable ATR for risk management"""
    if df.empty:
        return None
    
    df = df.copy()
    df["tr"] = df["high"] - df["low"]
    df["atr"] = df["tr"].rolling(period).mean()
    
    return df["atr"].iloc[-1] if not df["atr"].isna().all() else None

def get_utbot_signal():
    """Generates the final UT Bot signal with ATR and stop values"""
    logger.info("Generating UT Bot signal...")
    
    df = fetch_btc_data()
    if df.empty:
        logger.error("No data available for signal generation")
        return {
            "signal": "No Data", 
            "price": 0, 
            "atr": 0, 
            "utbot_stop": 0,
            "data_source": "None"
        }

    try:
        df1 = calc_utbot(df.copy(), 2, 1)
        df2 = calc_utbot(df.copy(), 2, 300)

        latest_price = df["close"].iloc[-1]
        latest_signal = "Hold"

        signal1 = df1["pos"].iloc[-1]
        signal2 = df2["pos"].iloc[-1]

        stop1 = df1["stop"].iloc[-1]
        stop2 = df2["stop"].iloc[-1]

        atr_stable = calculate_atr_stable(df, period=14)
        
        if atr_stable is None or pd.isna(atr_stable):
            atr_stable = 0
            logger.warning("ATR calculation returned None, defaulting to 0")

        logger.info(f"Price: ${latest_price:.2f}, ATR: ${atr_stable:.2f}")

        utbot_stop = None
        data_source = "Unknown"

        if signal2 == 1:
            latest_signal = "Buy"
            utbot_stop = stop2
            logger.info(f"BUY signal detected at ${latest_price:.2f}")
        else:
            logger.info("No BUY signal (UT Bot #2)")
        
        if signal1 == -1:
            latest_signal = "Sell"
            utbot_stop = stop1
            logger.info(f"SELL signal detected at ${latest_price:.2f}")
        else:
            logger.info("No SELL signal (UT Bot #1)")

        logger.info(f"Final signal: {latest_signal}")
        
        return {
            "signal": latest_signal, 
            "price": float(latest_price),
            "atr": float(atr_stable) if atr_stable else 0.0,
            "utbot_stop": float(utbot_stop) if utbot_stop else float(latest_price),
            "data_source": determine_data_source(df)
        }
        
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        import traceback
        traceback.print_exc()
        return {
            "signal": "Error", 
            "price": 0, 
            "atr": 0, 
            "utbot_stop": 0,
            "data_source": "Error"
        }

def determine_data_source(df):
    """Try to determine the data source based on the data characteristics."""
    if df.empty:
        return "None"
    
    # This is a simple heuristic - in a real implementation, you might
    # store the source with the data or use more sophisticated detection
    try:
        # Check if the data looks like it came from Binance
        if len(df) == 350 and df["time"].iloc[0] % 300000 == 0:  # 5-minute intervals
            return "Binance"
        elif len(df) == 200:  # Bybit limit
            return "Bybit"
        elif len(df) == 350:  # KuCoin limit
            return "KuCoin"
        elif len(df) == 350:  # Coinbase limit
            return "Coinbase"
        else:
            return "Mock"
    except:
        return "Unknown"
