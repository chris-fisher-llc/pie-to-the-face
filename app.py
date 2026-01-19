import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="DP Show Bet Tracker", page_icon="🥧", layout="wide")
DATA_SOURCE = "data/FULL_LEDGER.csv"

# The Main Cast for the Leaderboard
MAIN_CAST = ["Dan Patrick", "Paulie Pabst", "Todd Fritz", "Seton O'Connor", "Marvin Prince", "Dylan"]

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_SOURCE)
        # Convert Dates
        df['Bet Date'] = pd.to_datetime(df['Bet Date'], errors='coerce')
        df['Decision Date'] = pd.to_datetime(df['Decision Date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found. Please run the Accountant script.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.title("🥧 Bet Tracker")

# 1. Person Filter
all_people = sorted(list(set(df['Proposer'].unique()) | set(df['Acceptor'].unique())))
# Ensure Main Cast is at the top
sorted_people = [p for p in MAIN_CAST if p in all_people] + [p for p in all_people if p not in MAIN_CAST]
selected_person = st.sidebar.selectbox("Select Personality", ["All"] + sorted_people)

# 2. Status Filter
status_options = ["All"] + sorted(list(df['Status'].unique()))
selected_status = st.sidebar.selectbox("Filter by Status", status_options)

# --- FILTER LOGIC ---
if selected_person != "All":
    view_df = df[
        (df['Proposer'] == selected_person) | 
        (df['Acceptor'] == selected_person) |
        (df['Winner'] == selected_person) |
        (df['Loser'] == selected_person)
    ]
else:
    view_df = df

if selected_status != "All":
    view_df = view_df[view_df['Status'] == selected_status]

# --- SECTION 1: THE LEADERBOARD (Top Level) ---
st.header("🏆 The Scoreboard")

stats = []
for person in MAIN_CAST:
    # Use global dataframe for stats to ensure accuracy regardless of filters
    p_df = df 
    
    wins = len(p_df[p_df['Winner'] == person])
    losses = len(p_df[p_df['Loser'] == person])
    
    # Unpaid: Must be the Loser AND Status is Unpaid
    unpaid = len(p_df[(p_df['Loser'] == person) & (p_df['Status'] == 'Unpaid')])
    
    total_decided = wins + losses
    win_pct = (wins / total_decided * 100) if total_decided > 0 else 0.0
    
    stats.append({
        "Name": person,
        "Wins": wins,
        "Losses": losses,
        "Win %": f"{win_pct:.1f}%",
        "Unpaid Debts": unpaid
    })

stats_df = pd.DataFrame(stats).sort_values(by="Wins", ascending=False)

# Display Leaderboard
st.dataframe(
    stats_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Name": st.column_config.TextColumn("Member", width="medium"),
        "Win %": st.column_config.TextColumn("Win %"), # Formatted string
        "Unpaid Debts": st.column_config.NumberColumn(
            "Unpaid Debts 🚩", 
            help="Bets lost but not honored",
            format="%d"
        )
    }
)

# --- SECTION 2: DETAILED BET HISTORY ---
st.markdown("---")
st.subheader(f"📜 Bet Details ({len(view_df)} Records)")

# Sort: Unpaid first, then newest dates
view_df = view_df.sort_values(by=["Status", "Bet Date"], ascending=[False, False])

# Select Columns for Display
display_cols = [
    "Bet Date", "Summary", "Quote of Record", "Proposer", "Acceptor", 
    "Winner", "Loser", "Stake", "Status", 
    "Decision Date", "Confidence", "Reasoning"
]

# Rename for UI
display_df = view_df[display_cols].rename(columns={
    "Decision Date": "Outcome Date",
    "Confidence": "AI Projected Accuracy"
})

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Bet Date": st.column_config.DateColumn("Placed", format="MM/DD/YYYY"),
        "Outcome Date": st.column_config.DateColumn("Outcome", format="MM/DD/YYYY"),
        "Summary": st.column_config.TextColumn("Bet Condition", width="medium"),
        "Quote of Record": st.column_config.TextColumn("Transcript Quote", width="large", help="The exact moment the bet was made"),
        "Reasoning": st.column_config.TextColumn("AI Logic", width="large", help="Hover to read full reasoning"),
        "Status": st.column_config.Column("Status", width="small"),
        "AI Projected Accuracy": st.column_config.Column("AI Confidence", width="small"),
    }
)

# --- METRICS FOOTER ---
st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("Total Bets Visible", len(view_df))
c2.metric("Unpaid in View", len(view_df[view_df['Status'] == 'Unpaid']))
c3.metric("Pending in View", len(view_df[view_df['Status'] == 'Pending']))