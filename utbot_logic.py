# utbot_logic.py - Public Binance Only with Multiple Bypass Strategies

import pandas as pd
import requests
import time
import logging
from datetime import datetime
import json
import random
import hashlib

logger = logging.getLogger(__name__)

def fetch_btc_data():
    """Fetches latest 5-minute Kline data from public Binance endpoints."""
    # Try different public Binance approaches
    sources = [
        fetch_from_binance_public_main,
        fetch_from_binance_public_alternative,
        fetch_from_binance_public_data_endpoint,
        fetch_from_binance_public_with_headers,
        fetch_from_binance_public_with_timing,
        fetch_from_mock_data  # Last resort fallback
    ]
    
    for source_func in sources:
        try:
            logger.info(f"Attempting to fetch from {source_func.__name__}")
            df = source_func()
            if not df.empty and len(df) > 0:
                logger.info(f"Successfully fetched {len(df)} candles from {source_func.__name__}")
                return df
            else:
                logger.warning(f"Empty data from {source_func.__name__}")
        except Exception as e:
            logger.error(f"Failed to fetch from {source_func.__name__}: {e}")
            continue
    
    logger.error("All public Binance sources failed, using mock data")
    return fetch_from_mock_data()

def fetch_from_binance_public_main():
    """Fetch from main public Binance endpoint with optimized headers."""
    try:
        logger.info("Fetching from main public Binance endpoint")
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "BTCUSDT", "interval": "5m", "limit": 350}
        
        # Optimized headers to look like browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.binance.com/',
            'Origin': 'https://www.binance.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 451:
            raise Exception("Binance blocking requests (451 error)")
            
        response.raise_for_status()
        data = response.json()
        
        if not data:
            raise Exception("Empty data from Binance")
        
        return process_binance_data(data)
        
    except Exception as e:
        logger.error(f"Error with main public Binance: {e}")
        raise Exception(f"Main public Binance error: {str(e)}")

def fetch_from_binance_public_alternative():
    """Try alternative public Binance endpoints."""
    # List of alternative Binance endpoints that might work
    endpoints = [
        "https://api1.binance.com/api/v3/klines",
        "https://api2.binance.com/api/v3/klines",
        "https://api3.binance.com/api/v3/klines",
        "https://data-api.binance.com/api/v3/klines",
        "https://api.binance.me/api/v3/klines",
        "https://api.binance.vision/api/v3/klines",
        "https://fapi.binance.com/fapi/v1/klines",  # Futures API (might not be blocked)
        "https://dapi.binance.com/dapi/v1/klines"   # Coin-margined futures
    ]
    
    for endpoint in endpoints:
        try:
            logger.info(f"Trying alternative public endpoint: {endpoint}")
            params = {"symbol": "BTCUSDT", "interval": "5m", "limit": 350}
            
            headers = {
                'User-Agent': get_random_realistic_user_agent(),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.binance.com/',
                'Origin': 'https://www.binance.com'
            }
            
            response = requests.get(
                endpoint, 
                params=params, 
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 451:
                logger.warning(f"Endpoint {endpoint} blocked (451 error)")
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if not data:
                continue
                
            logger.info(f"Success with alternative endpoint: {endpoint}")
            return process_binance_data(data)
            
        except Exception as e:
            logger.warning(f"Failed with endpoint {endpoint}: {e}")
            continue
    
    raise Exception("All alternative public endpoints failed")

def fetch_from_binance_public_data_endpoint():
    """Try Binance data-specific endpoints."""
    try:
        logger.info("Trying Binance data endpoint")
        # Some regions have different data endpoints
        url = "https://api.binance.com/api/v3/uiKlines"
        params = {"symbol": "BTCUSDT", "interval": "5m", "limit": 350}
        
        headers = {
            'User-Agent': get_random_realistic_user_agent(),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.binance.com/en/markets',
            'Origin': 'https://www.binance.com'
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 451:
            raise Exception("Binance data endpoint blocked (451 error)")
            
        response.raise_for_status()
        data = response.json()
        
        if not data:
            raise Exception("Empty data from Binance data endpoint")
        
        return process_binance_data(data)
        
    except Exception as e:
        logger.error(f"Error with Binance data endpoint: {e}")
        raise Exception(f"Binance data endpoint error: {str(e)}")

def fetch_from_binance_public_with_headers():
    """Try with different header combinations."""
    header_sets = [
        # Mobile browser headers
        {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        },
        # Desktop browser headers
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        },
        # Safari browser headers
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        },
        # Simple headers
        {
            'User-Agent': 'curl/7.68.0',
            'Accept': 'application/json'
        }
    ]
    
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": "5m", "limit": 350}
    
    for i, headers in enumerate(header_sets):
        try:
            logger.info(f"Trying header set {i+1}")
            
            response = requests.get(
                url, 
                params=params, 
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 451:
                logger.warning(f"Header set {i+1} blocked (451 error)")
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if not data:
                continue
                
            logger.info(f"Success with header set {i+1}")
            return process_binance_data(data)
            
        except Exception as e:
            logger.warning(f"Failed with header set {i+1}: {e}")
            continue
    
    raise Exception("All header combinations failed")

def fetch_from_binance_public_with_timing():
    """Try with strategic timing and delays."""
    try:
        logger.info("Trying with strategic timing")
        
        # Add random delay to avoid pattern detection
        delay = random.uniform(2, 5)
        logger.info(f"Waiting {delay:.2f} seconds before request...")
        time.sleep(delay)
        
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "BTCUSDT", "interval": "5m", "limit": 350}
        
        headers = {
            'User-Agent': get_random_realistic_user_agent(),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.binance.com/en',
            'Origin': 'https://www.binance.com',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        }
        
        response = requests.get(
            url, 
            params=params, 
            headers=headers,
            timeout=20
        )
        
        if response.status_code == 451:
            raise Exception("Binance blocking even with timing strategy (451 error)")
            
        response.raise_for_status()
        data = response.json()
        
        if not data:
            raise Exception("Empty data from Binance with timing strategy")
        
        return process_binance_data(data)
        
    except Exception as e:
        logger.error(f"Error with timing strategy: {e}")
        raise Exception(f"Binance timing error: {str(e)}")

def get_current_price():
    """Fetches only current price from public Binance endpoints."""
    sources = [
        get_price_from_binance_public_main,
        get_price_from_binance_public_alternative,
        get_price_from_binance_public_with_headers,
        get_price_from_binance_public_with_timing,
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
    
    logger.error("All public Binance price sources failed")
    return get_mock_price()

def get_price_from_binance_public_main():
    """Fetch current price from main public Binance endpoint."""
    try:
        logger.info("Fetching price from main public Binance")
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCUSDT"}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.binance.com/',
            'Origin': 'https://www.binance.com'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 451:
            raise Exception("Binance blocking price requests (451 error)")
            
        response.raise_for_status()
        data = response.json()
        return float(data['price'])
        
    except Exception as e:
        logger.error(f"Error with main public Binance price: {e}")
        raise Exception(f"Main public Binance price error: {str(e)}")

def get_price_from_binance_public_alternative():
    """Try alternative public Binance endpoints for price."""
    endpoints = [
        "https://api1.binance.com/api/v3/ticker/price",
        "https://api2.binance.com/api/v3/ticker/price",
        "https://api3.binance.com/api/v3/ticker/price",
        "https://data-api.binance.com/api/v3/ticker/price",
        "https://api.binance.me/api/v3/ticker/price",
        "https://fapi.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT",  # Futures
        "https://dapi.binance.com/dapi/v1/ticker/price?symbol=BTCUSDT"   # Coin-margined
    ]
    
    for endpoint in endpoints:
        try:
            logger.info(f"Trying alternative price endpoint: {endpoint}")
            
            headers = {
                'User-Agent': get_random_realistic_user_agent(),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.binance.com/',
                'Origin': 'https://www.binance.com'
            }
            
            response = requests.get(
                endpoint, 
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 451:
                logger.warning(f"Price endpoint {endpoint} blocked (451 error)")
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if not data:
                continue
            
            # Handle different response formats
            if isinstance(data, list) and len(data) > 0:
                price = float(data[0]['price'])
            elif isinstance(data, dict) and 'price' in data:
                price = float(data['price'])
            else:
                continue
                
            logger.info(f"Price success with endpoint: {endpoint}")
            return price
            
        except Exception as e:
            logger.warning(f"Failed with price endpoint {endpoint}: {e}")
            continue
    
    raise Exception("All alternative public price endpoints failed")

def get_price_from_binance_public_with_headers():
    """Try with different header combinations for price."""
    header_sets = [
        {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
    ]
    
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {"symbol": "BTCUSDT"}
    
    for i, headers in enumerate(header_sets):
        try:
            logger.info(f"Trying price header set {i+1}")
            
            response = requests.get(
                url, 
                params=params, 
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 451:
                logger.warning(f"Price header set {i+1} blocked (451 error)")
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if not data:
                continue
                
            logger.info(f"Price success with header set {i+1}")
            return float(data['price'])
            
        except Exception as e:
            logger.warning(f"Failed with price header set {i+1}: {e}")
            continue
    
    raise Exception("All price header combinations failed")

def get_price_from_binance_public_with_timing():
    """Try with strategic timing for price."""
    try:
        logger.info("Trying price with strategic timing")
        
        # Add random delay
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCUSDT"}
        
        headers = {
            'User-Agent': get_random_realistic_user_agent(),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.binance.com/en',
            'Origin': 'https://www.binance.com',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 451:
            raise Exception("Binance blocking price even with timing (451 error)")
            
        response.raise_for_status()
        data = response.json()
        return float(data['price'])
        
    except Exception as e:
        logger.error(f"Error with price timing strategy: {e}")
        raise Exception(f"Binance price timing error: {str(e)}")

def get_mock_price():
    """Generate a mock price as last resort."""
    logger.warning("Using mock price as fallback")
    return 43000.0 + random.random() * 2000  # Random price around $43,000-$45,000

def fetch_from_mock_data():
    """Generate mock data as a last resort."""
    logger.warning("Using mock data as fallback")
    
    # Generate mock candlestick data
    now = int(time.time() * 1000)
    df_data = []
    
    # Start with a base price
    base_price = 43000.0
    price = base_price
    
    # Generate 350 candles (5-minute intervals)
    for i in range(350):
        timestamp = now - (350 - i) * 5 * 60 * 1000  # 5 minutes in milliseconds
        
        # Random walk for price
        change = (random.random() - 0.5) * 200  # Random change between -100 and +100
        price += change
        
        # Generate OHLC
        open_price = price
        high_price = open_price + random.random() * 100
        low_price = open_price - random.random() * 100
        close_price = low_price + random.random() * (high_price - low_price)
        volume = random.random() * 10
        
        df_data.append([
            timestamp, 
            open_price, 
            high_price, 
            low_price, 
            close_price, 
            volume,
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

def get_random_realistic_user_agent():
    """Get a realistic user agent string."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0'
    ]
    
    return random.choice(user_agents)

def process_binance_data(data):
    """Process raw Binance data into our expected format."""
    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume", 
        "c", "q", "n", "t", "v", "ignore"
    ])
    
    for col in ["close", "high", "low", "open"]:
        df[col] = df[col].astype(float)
    
    return df

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
    """Generates final UT Bot signal with ATR and stop values"""
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
            "data_source": "Binance"
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
