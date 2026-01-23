import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="DP Show Bet Tracker", page_icon="🥧", layout="wide")
DATA_SOURCE = "data/FULL_LEDGER.csv"
MAIN_CAST = ["Dan Patrick", "Paulie Pabst", "Todd Fritz", "Seton O'Connor", "Marvin Prince", "Dylan"]

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        # Read CSV
        df = pd.read_csv(DATA_SOURCE)
        
        # CRITICAL FIX: Fill missing values with empty strings to prevent 'float' errors
        df = df.fillna("")
        
        # Convert Dates
        df['Bet Date'] = pd.to_datetime(df['Bet Date'], errors='coerce')
        df['Decision Date'] = pd.to_datetime(df['Decision Date'], errors='coerce')
        
        # Generate ID if missing (backward compatibility)
        if 'Bet ID' not in df.columns:
            df['Bet ID'] = [f"BET-{i:03d}" for i in range(1, len(df)+1)]
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty: st.stop()

# --- SIDEBAR ---
st.sidebar.title("🥧 Bet Tracker")
all_people = sorted(list(set(df['Proposer'].unique()) | set(df['Acceptor'].unique())))
sorted_people = [p for p in MAIN_CAST if p in all_people] + [p for p in all_people if p not in MAIN_CAST]
selected_person = st.sidebar.selectbox("Select Personality", ["All"] + sorted_people)

status_options = ["All"] + sorted(list(df['Status'].unique()))
selected_status = st.sidebar.selectbox("Filter by Status", status_options)

# Filter Logic
if selected_person != "All":
    view_df = df[(df['Proposer'] == selected_person) | (df['Acceptor'] == selected_person) |
                 (df['Winner'] == selected_person) | (df['Loser'] == selected_person)]
else:
    view_df = df

if selected_status != "All":
    view_df = view_df[view_df['Status'] == selected_status]

view_df = view_df.sort_values(by=["Status", "Bet Date"], ascending=[False, False])

# --- 1. SCOREBOARD ---
st.header("🏆 The Scoreboard")
stats = []
for person in MAIN_CAST:
    p_df = df 
    wins = len(p_df[p_df['Winner'] == person])
    losses = len(p_df[p_df['Loser'] == person])
    unpaid = len(p_df[(p_df['Loser'] == person) & (p_df['Status'] == 'Unpaid')])
    total = wins + losses
    pct = (wins / total * 100) if total > 0 else 0.0
    stats.append({"Name": person, "Wins": wins, "Losses": losses, "Win %": f"{pct:.1f}%", "Unpaid Debts": unpaid})

st.dataframe(pd.DataFrame(stats).sort_values("Wins", ascending=False), use_container_width=True, hide_index=True,
             column_config={"Unpaid Debts": st.column_config.NumberColumn("Unpaid Bets 🚩", format="%d")})

st.markdown("---")

# --- 2. SUMMARY TABLE ---
st.header("📜 Bet History")
st.caption("Use the 'Bet ID' to see full details below.")

# Simplified Table (No long text)
display_cols = ["Bet ID", "Bet Date", "Summary", "Proposer", "Acceptor", "Winner", "Loser", "Stake", "Status"]

# Filter existing columns only
display_cols = [c for c in display_cols if c in view_df.columns]
display_df = view_df[display_cols].copy()

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Bet Date": st.column_config.DateColumn("Date", format="MM/DD/YYYY"),
        "Summary": st.column_config.TextColumn("Bet Condition", width="large"),
        "Status": st.column_config.Column("Status", width="small"),
    }
)

st.markdown("---")

# --- 3. DETAIL INSPECTOR ---
st.header("🔎 Bet Inspector")

# Dropdown for ID Selection
# FIX: Use str() to ensure it doesn't crash on empty summaries
bet_options = view_df.apply(lambda x: f"{x['Bet ID']} | {str(x['Summary'])[:60]}...", axis=1).tolist()

if bet_options:
    selected_option = st.selectbox("Select a Bet ID to inspect:", bet_options)
    # Extract ID
    selected_id = selected_option.split(" | ")[0]
    row = view_df[view_df['Bet ID'] == selected_id].iloc[0]

    with st.container(border=True):
        st.subheader(f"{row['Bet ID']}: {row['Proposer']} vs {row['Acceptor']}")
        st.markdown(f"**Condition:** {row['Summary']}")
        
        # Handle potentially missing 'Quote of Record' safely
        quote = row.get('Quote of Record', 'No quote available.')
        st.markdown(f"#### ❝ {quote} ❞")
        st.divider()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Winner", row['Winner'])
        c2.metric("Loser", row['Loser'])
        c3.metric("Status", row['Status'], delta="UNPAID" if row['Status']=='Unpaid' else None, delta_color="inverse")
        
        st.markdown("**AI Reasoning:**")
        st.info(row.get('Reasoning', 'No reasoning available.'))
