import csv
import os
from datetime import datetime
from typing import Optional

def ensure_journal_exists(filepath: str = "trading_journal.csv"):
    """Create journal file with headers if it doesn't exist"""
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['date', 'asset', 'change_pct', 'reason', 'emotion'])

def append_journal_entry(asset: str, change_pct: float, reason: str, emotion: str, 
                        filepath: str = "trading_journal.csv"):
    """Append a new entry to the trading journal"""
    ensure_journal_exists(filepath)
    
    with open(filepath, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            asset,
            change_pct,
            reason,
            emotion
        ])

def read_journal(filepath: str = "trading_journal.csv", limit: Optional[int] = None) -> list:
    """Read journal entries, optionally limited to recent entries"""
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, 'r', newline='') as file:
        reader = csv.DictReader(file)
        entries = list(reader)
        
        if limit:
            return entries[-limit:]
        return entries

def get_journal_stats(filepath: str = "trading_journal.csv") -> dict:
    """Get basic statistics from the journal"""
    entries = read_journal(filepath)
    
    if not entries:
        return {
            'total_entries': 0,
            'total_changes': 0,
            'avg_change': 0,
            'last_entry': None
        }
    
    total_entries = len(entries)
    changes = [float(entry['change_pct']) for entry in entries if entry['change_pct'].replace('-', '').replace('.', '').isdigit()]
    total_changes = sum(changes)
    avg_change = total_changes / len(changes) if changes else 0
    
    return {
        'total_entries': total_entries,
        'total_changes': total_changes,
        'avg_change': avg_change,
        'last_entry': entries[-1] if entries else None
    }