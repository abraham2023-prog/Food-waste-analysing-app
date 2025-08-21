import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
# Remove commas and convert numeric columns
numeric_cols = [
    "Begin month\ninventory", "Production", "Domestic", "Export",
    "Month-end \ninventory", "Shipment value\n(thousand baht)",
    "Capacity", "Estimated_Waste", "Waste_Percent_of_Production",
    "Shipment_value_per_ton", "Estimated_Waste_Value_(thousand_baht)"
]

df = df.replace({',': ''}, regex=True)
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Rename columns for consistency
df = df.rename(columns={
    "Begin month\ninventory": "begin_month_inventory",
    "Production": "production",
    "Domestic": "domestic",
    "Export": "export",
    "Month-end \ninventory": "month_end_inventory",
    "Shipment value\n(thousand baht)": "shipment_value_thousand_baht",
    "Capacity": "capacity",
    "Estimated_Waste": "estimated_waste",
    "Waste_Percent_of_Production": "waste_percent_of_production",
    "Shipment_value_per_ton": "shipment_value_per_ton",
    "Estimated_Waste_Value_(thousand_baht)": "estimated_waste_value_thousand_baht"
})

# Filter based on user selection
df_filtered = df[
    (df['Product'].isin(selected_products)) &
    (df['Year'] >= year_range[0]) &
    (df['Year'] <= year_range[1])
].copy()

# # -------------------- Derived Metrics --------------------
# # Calculate waste if 'Estimated_Waste' column is missing
# if 'Estimated_Waste' not in df_filtered.columns and 'estimated_waste' not in df_filtered.columns:
#     df_filtered['estimated_waste'] = (
#         df_filtered['begin_month_inventory'] + df_filtered['production']
#         - df_filtered['domestic'] - df_filtered['export'] - df_filtered['month_end_inventory']
#     )

df_filtered['waste'] = df_filtered['estimated_waste']
df_filtered['waste_rate'] = df_filtered['waste'] / df_filtered['production']
df_filtered['avg_inventory'] = (df_filtered['begin_month_inventory'] + df_filtered['month_end_inventory']) / 2
df_filtered['inventory_turnover'] = df_filtered['domestic'] / df_filtered['avg_inventory']
df_filtered['capacity_utilization'] = df_filtered['production'] / df_filtered['capacity']
df_filtered['value_per_unit'] = df_filtered['shipment_value_per_ton']
df_filtered['waste_value'] = df_filtered['estimated_waste_value_thousand_baht']

# -------------------- Tabs --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Waste Analysis", "Inventory Analysis", 
    "Production vs Demand", "Economic Impact"
])

# -------------------- Tab 1: Overview --------------------
with tab1:
    st.markdown('<p class="section-header">📊 Overview Metrics</p>', unsafe_allow_html=True)
    total_waste = df_filtered['waste'].sum()
    total_production = df_filtered['production'].sum()
    overall_waste_rate = total_waste / total_production
    total_waste_value = df_filtered['waste_value'].sum()
    avg_turnover = df_filtered['inventory_turnover'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Waste", f"{total_waste:,.0f} units")
    col2.metric("Overall Waste Rate", f"{overall_waste_rate:.2%}")
    col3.metric("Value of Waste", f"฿{total_waste_value:,.0f}")
    col4.metric("Avg Inventory Turnover", f"{avg_turnover:.2f}")
    
    # Waste Trends
    st.markdown("#### Waste Trends Over Time")
    waste_by_time = df_filtered.groupby(['Year', 'Month']).agg({'waste': 'sum'}).reset_index()
    waste_by_time['date'] = pd.to_datetime(waste_by_time['Year'].astype(str) + '-' + waste_by_time['Month'].astype(str))
    fig = px.line(waste_by_time, x='date', y='waste', title="Total Waste Over Time")
    st.plotly_chart(fig, use_container_width=True)
    
    # Waste by Product
    st.markdown("#### Waste by Product")
    waste_by_product = df_filtered.groupby('Product').agg({
        'waste': 'sum',
        'production': 'sum',
        'waste_value': 'sum'
    }).reset_index()
    waste_by_product['waste_rate'] = waste_by_product['waste'] / waste_by_product['production']
    
    col1, col2 = st.columns(2)
    fig = px.bar(waste_by_product, x='Product', y='waste', title="Total Waste by Product")
    col1.plotly_chart(fig, use_container_width=True)
    fig = px.bar(waste_by_product, x='Product', y='waste_rate', title="Waste Rate by Product")
    col2.plotly_chart(fig, use_container_width=True)

# -------------------- Tab 2: Waste Analysis --------------------
with tab2:
    st.markdown('<p class="section-header">📈 Waste Analysis</p>', unsafe_allow_html=True)
    waste_by_month = df_filtered.groupby(['Month', 'Product']).agg({'waste': 'mean'}).reset_index()
    fig = px.line(waste_by_month, x='Month', y='waste', color='Product', title="Average Waste by Month")
    st.plotly_chart(fig, use_container_width=True)
    
    fig = px.box(df_filtered, x='Product', y='waste', title="Distribution of Waste by Product")
    st.plotly_chart(fig, use_container_width=True)
    
    waste_by_year = df_filtered.groupby(['Year', 'Product']).agg({'waste': 'sum'}).reset_index()
    fig = px.bar(waste_by_year, x='Year', y='waste', color='Product', barmode='group', title="Total Waste by Year and Product")
    st.plotly_chart(fig, use_container_width=True)

# -------------------- Tab 3: Inventory Analysis --------------------
with tab3:
    st.markdown('<p class="section-header">📦 Inventory Analysis</p>', unsafe_allow_html=True)
    turnover_by_product = df_filtered.groupby('Product').agg({'inventory_turnover': 'mean'}).reset_index()
    fig = px.bar(turnover_by_product, x='Product', y='inventory_turnover', title="Average Inventory Turnover")
    st.plotly_chart(fig, use_container_width=True)
    
    df_filtered['days_of_supply'] = (df_filtered['month_end_inventory'] / df_filtered['domestic']) * 30
    days_supply_by_product = df_filtered.groupby('Product').agg({'days_of_supply': 'mean'}).reset_index()
    fig = px.bar(days_supply_by_product, x='Product', y='days_of_supply', title="Average Days of Supply")
    st.plotly_chart(fig, use_container_width=True)
    
    fig = px.scatter(df_filtered, x='avg_inventory', y='waste', color='Product', trendline="ols",
                     title="Inventory vs Waste")
    st.plotly_chart(fig, use_container_width=True)

# -------------------- Tab 4: Production vs Demand --------------------
with tab4:
    st.markdown('<p class="section-header">⚖️ Production vs Demand Analysis</p>', unsafe_allow_html=True)
    prod_vs_domestic = df_filtered.groupby('Product').agg({'production': 'sum', 'domestic': 'sum'}).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=prod_vs_domestic['Product'], y=prod_vs_domestic['production'], name='Production'))
    fig.add_trace(go.Bar(x=prod_vs_domestic['Product'], y=prod_vs_domestic['domestic'], name='Domestic'))
    fig.update_layout(barmode='group', title="Production vs Domestic Sales")
    st.plotly_chart(fig, use_container_width=True)
    
    df_filtered['production_demand_gap'] = df_filtered['production'] - df_filtered['domestic']
    gap_by_product = df_filtered.groupby('Product').agg({'production_demand_gap': 'mean'}).reset_index()
    fig = px.bar(gap_by_product, x='Product', y='production_demand_gap', title="Average Production-Demand Gap")
    st.plotly_chart(fig, use_container_width=True)
    
    fig = px.scatter(df_filtered, x='production', y='waste', color='Product', trendline="ols", title="Production vs Waste")
    st.plotly_chart(fig, use_container_width=True)

# -------------------- Tab 5: Economic Impact --------------------
with tab5:
    st.markdown('<p class="section-header">💰 Economic Impact Analysis</p>', unsafe_allow_html=True)
    waste_value_by_product = df_filtered.groupby('Product').agg({'waste_value': 'sum'}).reset_index()
    fig = px.bar(waste_value_by_product, x='Product', y='waste_value', title="Value of Waste by Product (Thousand Baht)")
    st.plotly_chart(fig, use_container_width=True)
    
    waste_value_by_month = df_filtered.groupby(['Year', 'Month']).agg({'waste_value': 'sum'}).reset_index()
    waste_value_by_month['date'] = pd.to_datetime(waste_value_by_month['Year'].astype(str) + '-' + waste_value_by_month['Month'].astype(str))
    fig = px.line(waste_value_by_month, x='date', y='waste_value', title="Waste Value Trends Over Time")
    st.plotly_chart(fig, use_container_width=True)
    
    total_values = df_filtered.groupby('Product').agg({'shipment_value_thousand_baht': 'sum', 'waste_value': 'sum'}).reset_index()
    total_values['waste_pct_of_value'] = total_values['waste_value'] / total_values['shipment_value_thousand_baht'] * 100
    fig = px.bar(total_values, x='Product', y='waste_pct_of_value', title="Waste Value as % of Shipment Value")
    st.plotly_chart(fig, use_container_width=True)

# -------------------- Download Results --------------------
st.sidebar.markdown("---")
st.sidebar.download_button(
    label="Download Analysis Results",
    data=df_filtered.to_csv(index=False),
    file_name="food_waste_analysis.csv",
    mime="text/csv"
)




