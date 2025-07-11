import time
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from telegram_utils import send_telegram_message
from journal import append_journal_entry

class TriggerEngine:
    def __init__(self):
        self.last_allocation = None
        self.last_trigger_time = {}
        self.cooldown_hours = 12
        
    def _should_trigger(self, trigger_name: str) -> bool:
        """Check if enough time has passed since last trigger"""
        now = time.time()
        last_time = self.last_trigger_time.get(trigger_name, 0)
        return (now - last_time) >= (self.cooldown_hours * 3600)
    
    def _record_trigger(self, trigger_name: str):
        """Record trigger time"""
        self.last_trigger_time[trigger_name] = time.time()
    
    def calculate_allocation(self, metrics: Dict) -> Tuple[float, float, float]:
        """Calculate BTC/ALTS/STABLES allocation based on metrics"""
        btc_dom = metrics.get('btc_dominance', 60)
        alt_index = metrics.get('alt_season_index', 50)
        
        if btc_dom >= 61 and alt_index < 50:
            return (0.70, 0.25, 0.05)  # BTC dominance phase
        elif btc_dom < 60 and alt_index >= 50:
            return (0.45, 0.50, 0.05)  # Alt season phase
        else:
            return (0.60, 0.35, 0.05)  # Neutral phase
    
    def check_rotation_triggers(self, metrics: Dict) -> Optional[str]:
        """Check BTC/ALT rotation triggers"""
        btc_dom = metrics.get('btc_dominance', 60)
        alt_index = metrics.get('alt_season_index', 50)
        
        trigger_name = "rotation"
        
        if btc_dom < 60 and alt_index > 50 and self._should_trigger(trigger_name):
            self._record_trigger(trigger_name)
            message = f"🔄 *BTC.D < 60% & alt momentum ↑* – start rotation.\nBTC Dom: {btc_dom:.1f}% | Alt Index: {alt_index:.1f}"
            send_telegram_message(message)
            append_journal_entry("ROTATION", -10, "BTC.D <60, rotate", "😐")
            return message
        
        return None
    
    def check_alt_season_triggers(self, metrics: Dict) -> Optional[str]:
        """Check alt season intensity triggers"""
        alt_index = metrics.get('alt_season_index', 50)
        
        # Full alt season
        if alt_index >= 75 and self._should_trigger("alt_season_full"):
            self._record_trigger("alt_season_full")
            message = f"🚀 *Full alt-season (≥ 75)*\nAlt Index: {alt_index:.1f}"
            send_telegram_message(message)
            append_journal_entry("ALTS", +25, "Full alt-season", "🚀")
            return message
        
        # Back to BTC dominance
        elif alt_index <= 25 and self._should_trigger("alt_season_end"):
            self._record_trigger("alt_season_end")
            message = f"📉 *Back to BTC dominance*\nAlt Index: {alt_index:.1f}"
            send_telegram_message(message)
            append_journal_entry("BTC", +20, "Back to BTC dominance", "📉")
            return message
        
        return None
    
    def check_funding_triggers(self, metrics: Dict) -> Optional[str]:
        """Check funding rate and leverage triggers"""
        btc_funding = metrics.get('btc_funding_rate', 0)
        hype_funding = metrics.get('hype_funding_rate', 0)
        
        messages = []
        
        # BTC funding check
        if abs(btc_funding) >= 0.10 and self._should_trigger("funding_btc"):
            self._record_trigger("funding_btc")
            message = f"⚠️ *Crowded leverage: BTC*\nFunding: {btc_funding:.3f}%/8h"
            send_telegram_message(message)
            append_journal_entry("BTC", -20, f"Crowded leverage: BTC. Funding {btc_funding:.3f}%", "⚠️")
            messages.append(message)
        
        # HYPE funding check
        if abs(hype_funding) >= 0.10 and self._should_trigger("funding_hype"):
            self._record_trigger("funding_hype")
            message = f"⚠️ *Crowded leverage: HYPE*\nFunding: {hype_funding:.3f}%/8h"
            send_telegram_message(message)
            append_journal_entry("HYPE", -20, f"Crowded leverage: HYPE. Funding {hype_funding:.3f}%", "⚠️")
            messages.append(message)
        
        return "; ".join(messages) if messages else None
    
    def check_stablecoin_triggers(self, metrics: Dict) -> Optional[str]:
        """Check stablecoin issuance triggers"""
        stable_delta = metrics.get('stablecoin_delta', 0)
        
        if stable_delta >= 1_000_000_000 and self._should_trigger("stablecoin_issuance"):
            self._record_trigger("stablecoin_issuance")
            message = f"💰 *New stable-coin issuance – ammo loaded*\n7d Change: ${stable_delta/1e9:.1f}B"
            send_telegram_message(message)
            append_journal_entry("STABLES", +10, "New stable-coin issuance", "💰")
            return message
        
        return None
    
    def check_macro_triggers(self, metrics: Dict) -> Optional[str]:
        """Check macro event triggers"""
        macro_events = metrics.get('macro_events', [])
        
        now = datetime.now()
        
        for event in macro_events:
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                time_diff = abs((event_date - now).total_seconds() / 3600)
                
                if time_diff <= 12 and self._should_trigger(f"macro_{event['event']}"):
                    self._record_trigger(f"macro_{event['event']}")
                    message = f"📅 *Macro in play: {event['event']}*\nDate: {event['date']}"
                    send_telegram_message(message)
                    append_journal_entry("CASH", 0, f"Macro in play: {event['event']}", "📅")
                    return message
            except Exception:
                continue
        
        return None
    
    def check_all_triggers(self, metrics: Dict) -> Dict:
        """Check all trigger conditions"""
        results = {
            'rotation': self.check_rotation_triggers(metrics),
            'alt_season': self.check_alt_season_triggers(metrics),
            'funding': self.check_funding_triggers(metrics),
            'stablecoin': self.check_stablecoin_triggers(metrics),
            'macro': self.check_macro_triggers(metrics)
        }
        
        # Calculate current allocation
        current_allocation = self.calculate_allocation(metrics)
        
        # Check if allocation changed
        if self.last_allocation and self.last_allocation != current_allocation:
            btc_change = (current_allocation[0] - self.last_allocation[0]) * 100
            message = f"📊 *Allocation Update*\nBTC: {current_allocation[0]:.0%} | ALTS: {current_allocation[1]:.0%} | STABLES: {current_allocation[2]:.0%}"
            send_telegram_message(message)
            append_journal_entry("ALLOCATION", btc_change, "Auto allocation update", "📊")
        
        self.last_allocation = current_allocation
        results['allocation'] = current_allocation
        
        return results