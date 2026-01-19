import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="DP Show Bet Tracker", page_icon="🥧", layout="wide")
DATA_SOURCE = "FULL_LEDGER.csv"

# The Main 5 Cast Members
MAIN_CAST = ["Dan Patrick", "Paulie Pabst", "Todd Fritz", "Seton O'Connor", "Marvin Prince"]

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_SOURCE)
        df['Bet Date'] = pd.to_datetime(df['Bet Date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found. Upload FULL_LEDGER.csv to your repo.")
    st.stop()

# --- NAME NORMALIZATION (Safety Net) ---
# Just in case the CSV has slight variations, we force them again here
def clean_name(name):
    if not isinstance(name, str): return "Other"
    n = name.lower()
    if "paul" in n: return "Paulie Pabst"
    if "todd" in n or "fritz" in n: return "Todd Fritz"
    if "seton" in n: return "Seton O'Connor"
    if "marvin" in n: return "Marvin Prince"
    if "dan" in n and "patrick" in n: return "Dan Patrick"
    return name # Keep callers/others as is

# Apply cleaning to the dataframe for display
df['Proposer'] = df['Proposer'].apply(clean_name)
df['Acceptor'] = df['Acceptor'].apply(clean_name)
df['Winner'] = df['Winner'].apply(clean_name)
df['Loser'] = df['Loser'].apply(clean_name)

# --- SIDEBAR ---
st.sidebar.title("🥧 Bet Tracker")
selected_person = st.sidebar.radio("Select Personality", ["All"] + MAIN_CAST)

# --- FILTERING ---
if selected_person != "All":
    # Show bets where they are Proposer OR Acceptor
    display_df = df[
        (df['Proposer'] == selected_person) | 
        (df['Acceptor'] == selected_person)
    ]
else:
    display_df = df

# --- SECTION 1: THE SCOREBOARD (Summary) ---
st.header(f"📊 The Scoreboard ({selected_person})")

stats = []
for person in MAIN_CAST:
    # Calculate Wins
    wins = len(df[df['Winner'] == person])
    
    # Calculate Losses (Paid + Unpaid + Pending Losses if identified)
    losses = len(df[df['Loser'] == person])
    
    # Calculate Unpaid Debts (Where they lost AND it's unpaid)
    unpaid = len(df[(df['Loser'] == person) & (df['Status'] == 'Unpaid')])
    
    # Win %
    total_decided = wins + losses
    win_pct = (wins / total_decided * 100) if total_decided > 0 else 0.0
    
    stats.append({
        "Personality": person,
        "Wins": wins,
        "Losses": losses,
        "Win %": f"{win_pct:.1f}%",
        "Unpaid Debts": unpaid
    })

stats_df = pd.DataFrame(stats).sort_values(by="Wins", ascending=False)

# If a specific person is selected, highlight them or show only them? 
# Usually better to show the full leaderboard for comparison, 
# but maybe filter if the user really wants focus.
# For now, we show the full table because context matters.

st.dataframe(
    stats_df, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Unpaid Debts": st.column_config.NumberColumn(
            "Unpaid Debts 🚩", help="Bets lost but not honored."
        )
    }
)

# --- SECTION 2: BET DETAILS ---
st.markdown("---")
st.header(f"📜 Bet History")

# Sort by Date (Newest first)
detail_view = display_df.sort_values(by="Bet Date", ascending=False)

# Select and Rename Columns for cleaner view
# We use 'Summary' (Condition) as the description
view_cols = [
    "Bet Date", "Episode", "Time", "Proposer", "Acceptor", 
    "Stake", "Summary", "Winner", "Status"
]

st.dataframe(
    detail_view[view_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Bet Date": st.column_config.DateColumn("Date", format="MM/DD/YYYY"),
        "Time": st.column_config.TextColumn("Time", help="Timestamp in episode"),
        "Summary": st.column_config.TextColumn("Bet Condition", width="large"),
        "Status": st.column_config.Column(
            "Status",
            help="Paid, Unpaid, or Pending",
            width="small"
        )
    }
)

# --- METRICS FOOTER ---
if selected_person != "All":
    st.markdown(f"**Total Bets Involved:** {len(display_df)}")
else:
    st.markdown(f"**Total Bets Tracked:** {len(df)}")
