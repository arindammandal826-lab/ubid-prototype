import pandas as pd
import random
import datetime
import hashlib
from faker import Faker
import difflib
import plotly.express as px
import streamlit as st

# --- INITIALIZATION ---
fake = Faker('en_IN')
st.set_page_config(page_title="KA Business Intelligence", layout="wide")

# --- PHASE 0: UBID GENERATOR ---
def generate_ubid():
    alphabet = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    entropy = "".join(random.choices(alphabet, k=8))
    checksum_char = alphabet[sum(alphabet.index(c) for c in entropy) % 34]
    return f"KA-{entropy}-{checksum_char}"

# --- PHASE 1: DATA GEN & SCRAMBLING ---
def scramble_pii(text):
    if not text: return None
    return hashlib.sha256(f"{text}_salt".encode()).hexdigest()[:16]

@st.cache_data
def load_mock_data():
    depts = ['Shop_Est', 'Factories', 'Labour', 'KSPCB']
    records = []
    for _ in range(60):
        base_name = fake.company()
        base_pan = fake.pystr(min_chars=10, max_chars=10).upper() if random.random() > 0.2 else None
        base_pin = "560058" if random.random() < 0.2 else fake.postcode()
        
        for dept in random.sample(depts, k=random.randint(1, 3)):
            records.append({
                'dept_source': dept,
                'business_name': base_name if random.random() > 0.2 else base_name[:5] + " Typo",
                'address': f"{fake.street_address()}, Bangalore",
                'pin_code': base_pin,
                'pan_number': base_pan,
                'scrambled_pan': scramble_pii(base_pan)
            })
    return pd.DataFrame(records)

# --- PHASE 2 & 3: RESOLUTION & HITL ---
def resolve_and_cluster(df):
    df['UBID'] = None
    df['Confidence'] = 0
    # Simple Deterministic Logic for Demo
    for pan in df['scrambled_pan'].dropna().unique():
        ubid = generate_ubid()
        df.loc[df['scrambled_pan'] == pan, ['UBID', 'Confidence']] = [ubid, 100]
    
    # Fill remaining with unique UBIDs (simulating new entities)
    unmatched = df[df['UBID'].isna()]
    for idx in unmatched.index:
        df.at[idx, 'UBID'] = generate_ubid()
        df.at[idx, 'Confidence'] = random.randint(50, 85)
    return df

# --- PHASE 6: THE DASHBOARD UI ---
def main():
    st.title("🏛️ Karnataka Unified Business Identifier (UBID)")
    st.markdown("### Active Business Intelligence Dashboard")
    
    # Data Pipeline
    df_raw = load_mock_data()
    df_resolved = resolve_and_cluster(df_raw)
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Records", len(df_raw))
    m2.metric("Unique UBIDs", df_resolved['UBID'].nunique())
    m3.metric("Avg Confidence", f"{int(df_resolved['Confidence'].mean())}%")

    # Visuals
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.pie(df_resolved, names='dept_source', title="Data Distribution by Department")
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.histogram(df_resolved, x='Confidence', title="Linkage Confidence Scores", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig2, use_container_width=True)

    # Query Interface (Phase 5)
    st.divider()
    st.subheader("🔍 Intelligence Query")
    target_pin = st.text_input("Search PIN Code", "560058")
    results = df_resolved[df_resolved['pin_code'] == target_pin]
    st.dataframe(results[['UBID', 'business_name', 'dept_source', 'Confidence']])

if __name__ == "__main__":
    main()

