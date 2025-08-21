import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# -------------------- Page Configuration --------------------
st.set_page_config(
    page_title="Food Waste Analysis Dashboard",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- Custom CSS --------------------
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #2e8b57; font-weight: 700;}
    .section-header {font-size: 1.8rem; color: #2e8b57; border-bottom: 2px solid #2e8b57; padding-bottom: 0.3rem;}
    .metric-label {font-weight: 600; color: #2e8b57;}
    .positive-metric {color: #228B22;}
    .negative-metric {color: #DC143C;}
    .info-text {background-color: #f0f8f0; padding: 15px; border-radius: 5px; border-left: 4px solid #2e8b57;}
</style>
""", unsafe_allow_html=True)

# -------------------- App Title --------------------
st.markdown('<p class="main-header">🍎 Food Waste Analysis Dashboard</p>', unsafe_allow_html=True)
st.markdown("Analyze food waste patterns from production and inventory data")

# -------------------- Load Data --------------------
with st.sidebar:
    st.header("Data Configuration")
    st.subheader("Upload Data")
    uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success("Data uploaded successfully!")
        
        # Show column names for debugging
        st.write("Columns in your dataset:", df.columns.tolist())
        
    else:
        st.info("Please upload your dataset to start analysis")
        st.stop()

    # -------------------- Analysis Parameters --------------------
    st.subheader("Select Products & Year Range")
    selected_products = st.multiselect(
        "Select Products to Analyze",
        options=df['Product'].unique(),
        default=df['Product'].unique()[:3]
    )
    
    year_range = st.slider(
        "Select Year Range",
        min_value=int(df['Year'].min()),
        max_value=int(df['Year'].max()),
        value=(int(df['Year'].min()), int(df['Year'].max()))
    )

# -------------------- Data Cleaning --------------------
# Create a copy of the dataframe for cleaning
df_clean = df.copy()

# Clean column names (remove newlines and extra spaces)
df_clean.columns = df_clean.columns.str.replace('\n', ' ').str.strip()

# Show available columns for debugging
st.write("Available columns after cleaning:", df_clean.columns.tolist())

# Define expected column names mapping with flexible matching
column_mapping = {}
possible_column_names = {
    'begin_inventory': ['begin month inventory', 'begin_inventory', 'starting inventory', 'initial inventory'],
    'production': ['production', 'prod'],
    'domestic': ['domestic', 'local sales', 'domestic sales'],
    'export': ['export', 'exports', 'export sales'],
    'end_inventory': ['month-end inventory', 'end inventory', 'ending inventory', 'final inventory', 'month_end_inventory'],
    'shipment_value': ['shipment value (thousand baht)', 'shipment_value', 'value', 'shipment value'],
    'capacity': ['capacity', 'production capacity'],
    'product': ['product', 'item', 'commodity'],
    'year': ['year', 'yr'],
    'month': ['month', 'mnth']
}

# Map columns based on what's available
for standard_name, possible_names in possible_column_names.items():
    for possible_name in possible_names:
        if possible_name in df_clean.columns:
            column_mapping[possible_name] = standard_name
            break

# Rename columns
df_clean = df_clean.rename(columns=column_mapping)
st.write("Columns after mapping:", df_clean.columns.tolist())

# Clean numeric columns
numeric_cols = ['begin_inventory', 'production', 'domestic', 'export', 
                'end_inventory', 'shipment_value', 'capacity']

for col in numeric_cols:
    if col in df_clean.columns:
        # Convert to string, remove commas and spaces, then convert to numeric
        df_clean[col] = (df_clean[col].astype(str)
                         .str.replace(',', '')
                         .str.replace(' ', '')
                         .replace('nan', np.nan)
                         .replace('', np.nan))
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

# Filter based on user selection
df_filtered = df_clean[
    (df_clean['product'].isin(selected_products)) &
    (df_clean['year'] >= year_range[0]) &
    (df_clean['year'] <= year_range[1])
].copy()

# -------------------- Derived Metrics --------------------
# Create default values for missing columns
required_columns = ['begin_inventory', 'production', 'domestic', 'export', 'end_inventory']
for col in required_columns:
    if col not in df_filtered.columns:
        df_filtered[col] = 0
        st.warning(f"Column '{col}' not found. Using default value of 0.")

# Calculate waste using the basic formula
df_filtered['waste'] = (
    df_filtered['begin_inventory'].fillna(0) + 
    df_filtered['production'].fillna(0) - 
    df_filtered['domestic'].fillna(0) - 
    df_filtered['export'].fillna(0) - 
    df_filtered['end_inventory'].fillna(0)
)

# Calculate total distribution
df_filtered['total_distribution'] = df_filtered['domestic'].fillna(0) + df_filtered['export'].fillna(0)

# Calculate other metrics with error handling
df_filtered['waste_rate'] = np.where(
    df_filtered['production'] > 0,
    df_filtered['waste'] / df_filtered['production'],
    0
)

df_filtered['avg_inventory'] = (
    df_filtered['begin_inventory'].fillna(0) + 
    df_filtered['end_inventory'].fillna(0)
) / 2

df_filtered['inventory_turnover'] = np.where(
    df_filtered['avg_inventory'] > 0,
    df_filtered['domestic'].fillna(0) / df_filtered['avg_inventory'],
    0
)

# Calculate capacity utilization if capacity column exists
if 'capacity' in df_filtered.columns:
    df_filtered['capacity_utilization'] = np.where(
        df_filtered['capacity'] > 0,
        df_filtered['production'].fillna(0) / df_filtered['capacity'],
        0
    )
else:
    df_filtered['capacity_utilization'] = 0

# Calculate value metrics if shipment_value exists
if 'shipment_value' in df_filtered.columns:
    df_filtered['value_per_unit'] = np.where(
        df_filtered['total_distribution'] > 0,
        df_filtered['shipment_value'].fillna(0) / df_filtered['total_distribution'],
        0
    )
    df_filtered['waste_value'] = df_filtered['waste'] * df_filtered['value_per_unit']
else:
    df_filtered['value_per_unit'] = 0
    df_filtered['waste_value'] = 0

# Replace infinite values and handle NaN
df_filtered = df_filtered.replace([np.inf, -np.inf], 0)
df_filtered = df_filtered.fillna(0)

# -------------------- Tabs --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Waste Analysis", "Inventory Analysis", 
    "Production vs Demand", "Economic Impact"
])

# -------------------- Tab 1: Overview --------------------
with tab1:
    st.markdown('<p class="section-header">📊 Overview Metrics</p>', unsafe_allow_html=True)
    
    # Calculate metrics
    total_waste = df_filtered['waste'].sum()
    total_production = df_filtered['production'].sum()
    overall_waste_rate = total_waste / total_production if total_production > 0 else 0
    total_waste_value = df_filtered['waste_value'].sum()
    avg_turnover = df_filtered['inventory_turnover'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Waste", f"{total_waste:,.0f} units")
    col2.metric("Overall Waste Rate", f"{overall_waste_rate:.2%}")
    col3.metric("Value of Waste", f"฿{total_waste_value:,.0f}")
    col4.metric("Avg Inventory Turnover", f"{avg_turnover:.2f}")
    
    # Waste Trends
    st.markdown("#### Waste Trends Over Time")
    waste_by_time = df_filtered.groupby(['year', 'month']).agg({'waste': 'sum'}).reset_index()
    waste_by_time['date'] = pd.to_datetime(waste_by_time['year'].astype(str) + '-' + waste_by_time['month'].astype(str))
    fig = px.line(waste_by_time, x='date', y='waste', title="Total Waste Over Time")
    st.plotly_chart(fig, use_container_width=True)
    
    # Waste by Product
    st.markdown("#### Waste by Product")
    waste_by_product = df_filtered.groupby('product').agg({
        'waste': 'sum',
        'production': 'sum',
        'waste_value': 'sum'
    }).reset_index()
    waste_by_product['waste_rate'] = np.where(
        waste_by_product['production'] > 0,
        waste_by_product['waste'] / waste_by_product['production'],
        0
    )
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(waste_by_product, x='product', y='waste', title="Total Waste by Product")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(waste_by_product, x='product', y='waste_rate', title="Waste Rate by Product")
        st.plotly_chart(fig, use_container_width=True)

# -------------------- Continue with other tabs (simplified for brevity) --------------------
with tab2:
    st.markdown('<p class="section-header">📈 Waste Analysis</p>', unsafe_allow_html=True)
    st.info("Waste analysis charts would appear here")

with tab3:
    st.markdown('<p class="section-header">📦 Inventory Analysis</p>', unsafe_allow_html=True)
    st.info("Inventory analysis charts would appear here")

with tab4:
    st.markdown('<p class="section-header">⚖️ Production vs Demand</p>', unsafe_allow_html=True)
    st.info("Production vs demand analysis charts would appear here")

with tab5:
    st.markdown('<p class="section-header">💰 Economic Impact</p>', unsafe_allow_html=True)
    st.info("Economic impact analysis charts would appear here")

# -------------------- Download Results --------------------
st.sidebar.markdown("---")
st.sidebar.download_button(
    label="Download Analysis Results",
    data=df_filtered.to_csv(index=False),
    file_name="food_waste_analysis.csv",
    mime="text/csv"
)

# Show final dataframe for debugging
st.write("Final processed data:", df_filtered.head())








