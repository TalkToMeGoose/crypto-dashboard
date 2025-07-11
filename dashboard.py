import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import time
from streamlit_autorefresh import st_autorefresh

from metrics import CryptoMetrics
from triggers import TriggerEngine
from journal import read_journal, get_journal_stats

# Page config
st.set_page_config(
    page_title="Crypto 3-Bucket Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh every 12 hours (43,200,000 ms)
st_autorefresh(interval=43_200_000, key="12h_refresh")

# Initialize components
@st.cache_resource
def init_components():
    metrics_client = CryptoMetrics()
    trigger_engine = TriggerEngine()
    return metrics_client, trigger_engine

def create_allocation_gauge(allocation_pct):
    """Create a gauge chart for portfolio allocation"""
    btc_pct, alt_pct, stable_pct = allocation_pct
    
    fig = go.Figure()
    
    # Add gauge
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = alt_pct * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "ALT Allocation %"},
        delta = {'reference': 35},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "orange"},
            'steps': [
                {'range': [0, 25], 'color': "lightgray"},
                {'range': [25, 50], 'color': "yellow"},
                {'range': [50, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def display_metrics_cards(metrics):
    """Display key metrics in card format"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "BTC Dominance",
            f"{metrics['btc_dominance']:.1f}%",
            delta=f"{metrics['btc_dominance'] - 60:.1f}%"
        )
    
    with col2:
        st.metric(
            "Alt Season Index",
            f"{metrics['alt_season_index']:.1f}",
            delta=f"{metrics['alt_season_index'] - 50:.1f}"
        )
    
    with col3:
        st.metric(
            "BTC Funding Rate",
            f"{metrics['btc_funding_rate']:.3f}%",
            delta=f"{metrics['btc_funding_rate'] - 0.1:.3f}%"
        )
    
    with col4:
        stable_delta_b = metrics['stablecoin_delta'] / 1e9
        st.metric(
            "Stablecoin 7d Δ",
            f"${stable_delta_b:.1f}B",
            delta=f"{stable_delta_b - 1:.1f}B"
        )

def display_allocation_recommendation(allocation):
    """Display current allocation recommendation"""
    btc_pct, alt_pct, stable_pct = allocation
    
    st.subheader("📊 Current Allocation Recommendation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🟡 BTC", f"{btc_pct:.0%}")
    
    with col2:
        st.metric("🟢 ALTS", f"{alt_pct:.0%}")
    
    with col3:
        st.metric("🔵 STABLES", f"{stable_pct:.0%}")

def display_triggers_status(trigger_results):
    """Display current trigger status"""
    st.subheader("🚨 Active Triggers")
    
    active_triggers = [k for k, v in trigger_results.items() if v and k != 'allocation']
    
    if active_triggers:
        for trigger in active_triggers:
            st.warning(f"**{trigger.title()}**: {trigger_results[trigger]}")
    else:
        st.success("No active triggers")

def display_journal_summary():
    """Display recent journal entries"""
    st.subheader("📝 Trading Journal")
    
    stats = get_journal_stats()
    recent_entries = read_journal(limit=10)
    
    if stats['total_entries'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Entries", stats['total_entries'])
            st.metric("Avg Change", f"{stats['avg_change']:.1f}%")
        
        with col2:
            if stats['last_entry']:
                st.write("**Last Entry:**")
                st.write(f"Date: {stats['last_entry']['date']}")
                st.write(f"Asset: {stats['last_entry']['asset']}")
                st.write(f"Change: {stats['last_entry']['change_pct']}%")
                st.write(f"Reason: {stats['last_entry']['reason']}")
        
        if recent_entries:
            st.write("**Recent Entries:**")
            df = pd.DataFrame(recent_entries)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No journal entries yet")

def main():
    st.title("📊 Crypto 3-Bucket Dashboard")
    st.markdown("*Smart allocation signals for BTC • ALTS • STABLES*")
    
    # Initialize
    metrics_client, trigger_engine = init_components()
    
    # Sidebar controls
    st.sidebar.header("⚙️ Controls")
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (12h)", value=True)
    
    # Load data
    with st.spinner("Loading market data..."):
        metrics = metrics_client.get_all_metrics()
        trigger_results = trigger_engine.check_all_triggers(metrics)
    
    # Display last updated
    st.sidebar.write(f"**Last Updated:** {datetime.fromtimestamp(metrics['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Main dashboard
    display_metrics_cards(metrics)
    
    st.divider()
    
    # Allocation section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        display_allocation_recommendation(trigger_results['allocation'])
    
    with col2:
        gauge_fig = create_allocation_gauge(trigger_results['allocation'])
        st.plotly_chart(gauge_fig, use_container_width=True)
    
    st.divider()
    
    # Triggers and journal
    col1, col2 = st.columns(2)
    
    with col1:
        display_triggers_status(trigger_results)
    
    with col2:
        display_journal_summary()
    
    # Detailed metrics in expander
    with st.expander("📈 Detailed Metrics"):
        st.json(metrics)
    
    # Macro events
    if metrics['macro_events']:
        st.subheader("📅 Upcoming Macro Events")
        for event in metrics['macro_events']:
            st.write(f"**{event['event']}** - {event['date']}")

if __name__ == "__main__":
    main()