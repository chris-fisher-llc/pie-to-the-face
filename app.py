import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="DP Show Bet Tracker", page_icon="🥧", layout="wide")
DATA_SOURCE = "FULL_LEDGER.csv"

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

# Sort: Unpaid first, then newest
view_df = view_df.sort_values(by=["Status", "Bet Date"], ascending=[False, False])

# --- SECTION 1: THE SCOREBOARD (Top Level) ---
st.header("🏆 The Scoreboard")

stats = []
for person in MAIN_CAST:
    # Use global dataframe for stats
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

st.dataframe(
    stats_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Name": st.column_config.TextColumn("Member", width="medium"),
        "Unpaid Debts": st.column_config.NumberColumn(
            "Unpaid Debts 🚩", 
            help="Bets lost but not honored",
            format="%d"
        )
    }
)

st.markdown("---")

# --- SECTION 2: MASTER-DETAIL VIEW ---
st.subheader("📜 Bet Inspector")

# Layout: 2 Columns
col_master, col_detail = st.columns([2, 3])

with col_master:
    st.markdown("### 1. Select a Bet")
    
    # Prepare a clean table for selection
    # We use a selectbox for "Master" selection as it's the most robust across Streamlit versions
    # Create a unique label for each bet
    view_df['Label'] = view_df.apply(
        lambda x: f"{x['Bet Date'].strftime('%m/%d/%y')} - {x['Proposer']} vs {x['Acceptor']}: {x['Summary'][:50]}...", 
        axis=1
    )
    
    bet_options = view_df['Label'].tolist()
    
    if bet_options:
        selected_label = st.selectbox("Choose from list:", bet_options, index=0)
        # Find the row that matches this label
        selected_row = view_df[view_df['Label'] == selected_label].iloc[0]
    else:
        st.info("No bets match current filters.")
        st.stop()

with col_detail:
    st.markdown("### 2. Bet Details")
    
    # Create a Card-like container
    with st.container(border=True):
        # Header
        st.subheader(f"{selected_row['Proposer']} vs. {selected_row['Acceptor']}")
        st.caption(f"Placed on: {selected_row['Bet Date'].strftime('%B %d, %Y')}")
        
        # The Quote (Hero Content)
        st.markdown(f"#### ❝ {selected_row['Quote of Record']} ❞")
        
        st.divider()
        
        # Key Stats Grid
        m1, m2, m3 = st.columns(3)
        m1.metric("Status", selected_row['Status'], 
                 delta="UNPAID" if selected_row['Status']=="Unpaid" else None, 
                 delta_color="inverse")
        m2.metric("Winner", selected_row['Winner'])
        m3.metric("Loser", selected_row['Loser'])
        
        m4, m5, m6 = st.columns(3)
        m4.metric("Stake", selected_row['Stake'] if pd.notna(selected_row['Stake']) else "N/A")
        m5.metric("Outcome Date", 
                 selected_row['Decision Date'].strftime('%m/%d/%y') if pd.notna(selected_row['Decision Date']) else "Pending")
        m6.metric("AI Accuracy", selected_row['Confidence'])
        
        st.divider()
        
        # Expandable Logic
        with st.expander("🔎 See AI Logic & Evidence"):
            st.markdown("**Reasoning:**")
            st.write(selected_row['Reasoning'])
            
            st.markdown("**Search Verification:**")
            st.info(selected_row['Search Context'])

# --- METRICS FOOTER ---
st.markdown("---")
f1, f2, f3 = st.columns(3)
f1.metric("Total Bets Visible", len(view_df))
f2.metric("Unpaid in View", len(view_df[view_df['Status'] == 'Unpaid']))
f3.metric("Pending in View", len(view_df[view_df['Status'] == 'Pending']))
