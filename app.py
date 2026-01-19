import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="DP Show Wall of Shame", page_icon="🥧", layout="wide")

# Point this to your raw GitHub URL if deploying! 
# e.g. "https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/data/FULL_LEDGER.csv"
DATA_SOURCE = "data/FULL_LEDGER.csv" 

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_SOURCE)
        # Ensure dates are datetime objects
        df['Bet Date'] = pd.to_datetime(df['Bet Date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found in the ledger.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter the Ledger")
all_guys = sorted(list(set(df['Proposer'].unique()) | set(df['Acceptor'].unique())))
if "Unknown" in all_guys: all_guys.remove("Unknown")

selected_guy = st.sidebar.selectbox("Select a Danette", ["All"] + all_guys)

if selected_guy != "All":
    # Filter where the person is EITHER the proposer OR the acceptor
    filtered_df = df[(df['Proposer'] == selected_guy) | (df['Acceptor'] == selected_guy)]
else:
    filtered_df = df

# --- TITLE & METRICS ---
st.title("🥧 The Dan Patrick Show: Wall of Shame")
st.markdown("Tracking every pie bet, every loss, and every unpaid debt on the show.")

# Calculate High-Level Stats
total_bets = len(df)
unpaid_bets = df[df['Status'] == 'Unpaid']
total_unpaid = len(unpaid_bets)
shame_rate = (total_unpaid / total_bets * 100) if total_bets > 0 else 0

# Metrics Row
c1, c2, c3 = st.columns(3)
c1.metric("Total Bets Tracked", total_bets)
c2.metric("Outstanding Debts", total_unpaid, delta_color="inverse")
c3.metric("Delinquency Rate", f"{shame_rate:.1f}%")

st.markdown("---")

# --- SECTION 1: THE WALL OF SHAME (Unpaid Bets) ---
st.header("🚫 The Wall of Shame (Unpaid Debts)")

# Filter for unpaid only
shame_df = filtered_df[filtered_df['Status'] == 'Unpaid'].copy()

if not shame_df.empty:
    # Sort by oldest first (Shame grows with time)
    shame_df = shame_df.sort_values(by='Bet Date', ascending=True)
    
    # Display cleaner table
    display_cols = ['Bet Date', 'Acceptor', 'Stake', 'Proposer', 'Original Snippet']
    st.dataframe(
        shame_df[display_cols],
        column_config={
            "Bet Date": st.column_config.DateColumn("Date"),
            "Acceptor": "Debtor (Loser)",
            "Proposer": "Owed To",
            "Original Snippet": st.column_config.TextColumn("Evidence", width="large")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("No unpaid debts found! The ledger is clean.")

st.markdown("---")

# --- SECTION 2: THE LEADERBOARD (Stats) ---
st.header("🏆 The Leaderboard")

# Create Stats DataFrame
stats = []
for person in all_guys:
    
    # Wins: Listed as Winner
    wins = len(df[df['Winner'] == person])
    
    # Losses: Listed as Loser (Paid + Unpaid)
    losses = len(df[df['Loser'] == person])
    
    # Unpaid: Listed as Loser AND Status is Unpaid
    unpaid = len(df[(df['Loser'] == person) & (df['Status'] == 'Unpaid')])
    
    total_decided = wins + losses
    win_pct = (wins / total_decided * 100) if total_decided > 0 else 0.0
    
    if total_decided > 0: # Only show active bettors
        stats.append({
            "Name": person,
            "Wins": wins,
            "Losses": losses,
            "Win %": win_pct,
            "Unpaid Debts": unpaid,
            "Total Bets": total_decided
        })

if stats:
    stats_df = pd.DataFrame(stats).sort_values(by="Wins", ascending=False)

    # FIX: Safely calculate max value and cast to standard int
    max_unpaid_val = int(stats_df['Unpaid Debts'].max()) if not stats_df.empty else 10
    if max_unpaid_val == 0: max_unpaid_val = 1 # Prevent div by zero in progress bar logic

    c_table, c_chart = st.columns([1, 1])

    with c_table:
        st.dataframe(
            stats_df,
            column_config={
                "Win %": st.column_config.NumberColumn(format="%.1f%%"),
                "Unpaid Debts": st.column_config.ProgressColumn(
                    "Shame Meter", 
                    format="%d", 
                    min_value=0, 
                    max_value=max_unpaid_val
                ),
            },
            use_container_width=True,
            hide_index=True
        )

    with c_chart:
        # Simple Bar Chart of Wins vs Losses
        if not stats_df.empty:
            # Melt for plotting
            melted = stats_df.melt(id_vars=["Name"], value_vars=["Wins", "Losses"], var_name="Result", value_name="Count")
            fig = px.bar(melted, x="Name", y="Count", color="Result", barmode="group", 
                        color_discrete_map={"Wins": "#2ecc71", "Losses": "#e74c3c"})
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No active bet stats available yet.")

# --- SECTION 3: RECENT ACTIVITY ---
st.markdown("---")
st.header("Recent Activity")
recent_df = filtered_df.sort_values(by='Bet Date', ascending=False).head(10)
st.dataframe(recent_df[['Bet Date', 'Proposer', 'Acceptor', 'Stake', 'Status', 'Winner']], use_container_width=True, hide_index=True)
