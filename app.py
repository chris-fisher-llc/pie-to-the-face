import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="DP Show Bet Tracker", page_icon="🥧", layout="wide")
DATA_SOURCE = "FULL_LEDGER.csv"
MAIN_CAST = ["Dan Patrick", "Paulie Pabst", "Todd Fritz", "Seton O'Connor", "Marvin Prince", "Dylan"]

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        # Read CSV
        df = pd.read_csv(DATA_SOURCE)
        
        # Fill missing values to prevent crashes
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

# Create a clean list for the dropdown
# We map partial matches (e.g. "Marvin") to full names ("Marvin Prince") for sorting
sorted_people = []
for person in MAIN_CAST:
    sorted_people.append(person)
    
# Add anyone else found in the data who isn't in the main cast
for p in all_people:
    if not any(main in p or p in main for main in MAIN_CAST):
        sorted_people.append(p)

selected_person = st.sidebar.selectbox("Select Personality", ["All"] + sorted_people)

status_options = ["All"] + sorted(list(df['Status'].unique()))
selected_status = st.sidebar.selectbox("Filter by Status", status_options)

# Filter Logic (Robust String Matching)
if selected_person != "All":
    # Check if the selected person is part of the name string
    # e.g. "Marvin" should match "Marvin Prince"
    mask = (
        df['Proposer'].str.contains(selected_person, case=False, na=False) | 
        df['Acceptor'].str.contains(selected_person, case=False, na=False) |
        df['Winner'].str.contains(selected_person, case=False, na=False) | 
        df['Loser'].str.contains(selected_person, case=False, na=False)
    )
    view_df = df[mask]
else:
    view_df = df

if selected_status != "All":
    view_df = view_df[view_df['Status'] == selected_status]

view_df = view_df.sort_values(by=["Status", "Bet Date"], ascending=[False, False])

# --- 1. SCOREBOARD (Robust Matching) ---
st.header("🏆 The Scoreboard")
stats = []
for person in MAIN_CAST:
    # We split the name to handle "Marvin" vs "Marvin Prince"
    # Logic: If "Marvin" is in the Winner column, count it.
    first_name = person.split()[0]
    
    p_df = df 
    
    # Wins: Count if Full Name OR First Name is in the Winner column
    wins = len(p_df[p_df['Winner'].str.contains(first_name, case=False, na=False)])
    
    # Losses
    losses = len(p_df[p_df['Loser'].str.contains(first_name, case=False, na=False)])
    
    # Unpaid
    unpaid = len(p_df[
        (p_df['Loser'].str.contains(first_name, case=False, na=False)) & 
        (p_df['Status'] == 'Unpaid')
    ])
    
    total = wins + losses
    pct = (wins / total * 100) if total > 0 else 0.0
    stats.append({"Name": person, "Wins": wins, "Losses": losses, "Win %": f"{pct:.1f}%", "Unpaid Debts": unpaid})

st.dataframe(pd.DataFrame(stats).sort_values("Wins", ascending=False), use_container_width=True, hide_index=True,
             column_config={"Unpaid Debts": st.column_config.NumberColumn("Unpaid Bets 🚩", format="%d")})

st.markdown("---")

# --- 2. SUMMARY TABLE (Interactive) ---
st.header("📜 Bet History")
st.caption("👆 Click on any row below to inspect the full details.")

display_cols = ["Bet ID", "Bet Date", "Summary", "Proposer", "Acceptor", "Winner", "Loser", "Stake", "Status"]
display_cols = [c for c in display_cols if c in view_df.columns]
display_df = view_df[display_cols].copy()

selection = st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Bet Date": st.column_config.DateColumn("Date", format="MM/DD/YYYY"),
        "Summary": st.column_config.TextColumn("Bet Condition", width="large"),
        "Status": st.column_config.Column("Status", width="small"),
    },
    selection_mode="single-row",
    on_select="rerun"
)

st.markdown("---")

# --- 3. DETAIL INSPECTOR ---
st.header("🔎 Bet Inspector")

if len(selection.selection.rows) > 0:
    selected_index = selection.selection.rows[0]
    selected_bet_id = display_df.iloc[selected_index]["Bet ID"]
    row = view_df[view_df['Bet ID'] == selected_bet_id].iloc[0]

    with st.container(border=True):
        st.subheader(f"{row['Bet ID']}: {row['Proposer']} vs {row['Acceptor']}")
        
        meta_info = f"Placed on: **{row['Bet Date'].strftime('%B %d, %Y')}**"
        if 'Time' in row and row['Time']:
             meta_info += f" @ **{row['Time']}**"
        st.markdown(meta_info)
        
        if 'Episode' in row and row['Episode']:
            st.caption(f"📺 Episode: {row['Episode']}")
            
        st.divider()
        st.markdown(f"**Condition:** {row['Summary']}")
        
        quote = row.get('Quote of Record', 'No quote available.')
        st.markdown(f"#### ❝ {quote} ❞")
        st.divider()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Winner", row['Winner'])
        c2.metric("Loser", row['Loser'])
        c3.metric("Status", row['Status'], delta="UNPAID" if row['Status']=='Unpaid' else None, delta_color="inverse")
        
        st.markdown("### 🧠 AI Reasoning")
        st.info(f"{row.get('Reasoning', 'No reasoning available.')}")
        
else:
    st.info("👈 Select a bet from the table above to see the AI analysis, quotes, and reasoning.")
