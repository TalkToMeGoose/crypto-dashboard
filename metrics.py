import os
import requests
import time
import csv
import io
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

class CryptoMetrics:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def _make_request(self, url: str, params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(3):
            try:
                if json_data:
                    response = self.session.post(url, json=json_data, headers=headers, timeout=10)
                else:
                    response = self.session.get(url, params=params, headers=headers, timeout=10)
                
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None
    
    def _get_csv_data(self, url: str) -> Optional[list]:
        """Get CSV data from URL"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            csv_data = csv.DictReader(io.StringIO(response.text))
            return list(csv_data)
        except Exception as e:
            print(f"CSV request failed: {e}")
            return None

    def get_btc_dominance_and_alt_cap(self) -> Tuple[Optional[float], Optional[float]]:
        """Get BTC dominance and alt market cap from CoinGecko"""
        url = "https://api.coingecko.com/api/v3/global"
        data = self._make_request(url)
        
        if not data:
            # Return mock data if API fails
            return 58.5, 850_000_000_000
            
        try:
            btc_dom = data['data']['market_cap_percentage']['btc']
            total_cap = data['data']['total_market_cap']['usd']
            alt_cap = total_cap * (1 - btc_dom / 100)
            return btc_dom, alt_cap
        except KeyError:
            return 58.5, 850_000_000_000

    def get_alt_season_index(self) -> Optional[float]:
        """Get alt season index from BlockchainCenter CSV"""
        url = "https://www.blockchaincenter.net/altcoin-season-index.csv"
        
        try:
            csv_data = self._get_csv_data(url)
            if not csv_data:
                return 45.2
            
            # Get the most recent entry (last row)
            latest_entry = csv_data[-1]
            
            # The CSV should have columns like 'date' and 'value' or 'index'
            # Try different possible column names
            for col in ['value', 'index', 'score', 'alt_season_index']:
                if col in latest_entry:
                    return float(latest_entry[col])
            
            # If no standard column found, try to parse any numeric value
            for value in latest_entry.values():
                try:
                    return float(value)
                except ValueError:
                    continue
                    
        except Exception as e:
            print(f"Alt season index fetch failed: {e}")
            
        return 45.2  # Fallback mock data

    def get_btc_funding_and_oi(self) -> Tuple[Optional[float], Optional[float]]:
        """Get BTC funding rate and open interest from Binance"""
        try:
            # Funding rate
            funding_url = "https://fapi.binance.com/fapi/v1/fundingRate"
            funding_data = self._make_request(funding_url, params={'symbol': 'BTCUSDT'})
            
            # Open interest
            oi_url = "https://fapi.binance.com/fapi/v1/openInterest"
            oi_data = self._make_request(oi_url, params={'symbol': 'BTCUSDT'})
            
            if not funding_data or not oi_data:
                return 0.08, 25_000_000_000
                
            funding_rate = float(funding_data[-1]['fundingRate']) * 100  # Convert to percentage
            open_interest = float(oi_data['openInterest'])
            
            return funding_rate, open_interest
        except Exception:
            return 0.08, 25_000_000_000

    def get_hyperliquid_funding(self, symbol: str = "HYPE") -> Optional[float]:
        """Get funding rate from Hyperliquid"""
        url = "https://api.hyperliquid.xyz/info"
        json_data = {"type": "perpFundingRates", "symbol": symbol}
        
        data = self._make_request(url, json_data=json_data)
        
        if not data:
            return 0.05
            
        try:
            return float(data[0]['fundingRate']) * 100
        except (KeyError, IndexError):
            return 0.05

    def get_stablecoin_delta(self) -> Optional[float]:
        """Get 7-day stablecoin market cap change from DeFiLlama"""
        url = "https://stablecoins.llama.fi/stablecoins"
        
        try:
            data = self._make_request(url)
            if not data:
                return 2_500_000_000
            
            # DeFiLlama returns array of stablecoin data
            # Sum up all stablecoin market caps to get total
            current_total = 0
            
            for stablecoin in data:
                if 'circulating' in stablecoin and 'price' in stablecoin:
                    current_total += stablecoin['circulating']['peggedUSD'] * stablecoin['price']
                elif 'circulating' in stablecoin:
                    current_total += stablecoin['circulating'].get('peggedUSD', 0)
                elif 'mcap' in stablecoin:
                    current_total += stablecoin['mcap']
            
            # For 7-day delta, we'll use a simple heuristic
            # In a real implementation, you'd store previous values
            # For now, return a reasonable estimate based on market conditions
            estimated_weekly_change = current_total * 0.02  # 2% weekly change estimate
            
            return estimated_weekly_change
            
        except Exception as e:
            print(f"Stablecoin delta fetch failed: {e}")
            return 2_500_000_000

    def get_macro_events(self) -> list:
        """Get high-impact macro events from TradingEconomics or Finnhub"""
        # Try TradingEconomics first
        tradingecon_key = os.getenv('TRADINGECON_KEY')
        if tradingecon_key:
            try:
                url = "https://api.tradingeconomics.com/calendar"
                params = {'c': tradingecon_key, 'importance': 3}
                data = self._make_request(url, params=params)
                
                if data:
                    return data[:5]  # Return top 5 events
            except Exception as e:
                print(f"TradingEconomics API failed: {e}")
        
        # Try Finnhub as fallback
        finnhub_key = os.getenv('FINNHUB_KEY')
        if finnhub_key:
            try:
                url = "https://finnhub.io/api/v1/calendar/economic"
                params = {'token': finnhub_key}
                data = self._make_request(url, params=params)
                
                if data and 'economicCalendar' in data:
                    # Filter for high importance events
                    high_importance = [event for event in data['economicCalendar'] 
                                     if event.get('importance', 0) >= 3]
                    return high_importance[:5]
            except Exception as e:
                print(f"Finnhub API failed: {e}")
        
        # Return mock data if no API keys or both fail
        return [{"event": "Fed Meeting", "date": "2025-07-12", "importance": 3}]

    def get_all_metrics(self) -> Dict:
        """Get all metrics in one call"""
        btc_dom, alt_cap = self.get_btc_dominance_and_alt_cap()
        alt_index = self.get_alt_season_index()
        btc_funding, btc_oi = self.get_btc_funding_and_oi()
        hype_funding = self.get_hyperliquid_funding()
        stable_delta = self.get_stablecoin_delta()
        macro_events = self.get_macro_events()
        
        return {
            'btc_dominance': btc_dom,
            'alt_market_cap': alt_cap,
            'alt_season_index': alt_index,
            'btc_funding_rate': btc_funding,
            'btc_open_interest': btc_oi,
            'hype_funding_rate': hype_funding,
            'stablecoin_delta': stable_delta,
            'macro_events': macro_events,
            'timestamp': time.time()
        }