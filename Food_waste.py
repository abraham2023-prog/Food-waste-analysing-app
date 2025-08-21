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
    "Capacity"
]

# Clean column names and handle data conversion
df = df.rename(columns={
    "Begin month\ninventory": "begin_month_inventory",
    "Production": "production",
    "Domestic": "domestic",
    "Export": "export",
    "Month-end \ninventory": "month_end_inventory",
    "Shipment value\n(thousand baht)": "shipment_value_thousand_baht",
    "Capacity": "capacity"
})

# Remove commas and convert to numeric
for col in ['begin_month_inventory', 'production', 'domestic', 'export', 
            'month_end_inventory', 'shipment_value_thousand_baht', 'capacity']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '')
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Filter based on user selection
df_filtered = df[
    (df['Product'].isin(selected_products)) &
    (df['Year'] >= year_range[0]) &
    (df['Year'] <= year_range[1])
].copy()

# -------------------- Derived Metrics --------------------
# Calculate waste based on available columns
df_filtered['waste'] = (
    df_filtered['begin_month_inventory'] + df_filtered['production']
    - df_filtered['domestic'] - df_filtered['export'] - df_filtered['month_end_inventory']
)

# Calculate total if not present
df_filtered['total'] = df_filtered['domestic'] + df_filtered['export']

# Calculate other metrics with error handling
df_filtered['waste_rate'] = df_filtered['waste'] / df_filtered['production'].replace(0, np.nan)
df_filtered['avg_inventory'] = (df_filtered['begin_month_inventory'] + df_filtered['month_end_inventory']) / 2
df_filtered['inventory_turnover'] = df_filtered['domestic'] / df_filtered['avg_inventory'].replace(0, np.nan)
df_filtered['capacity_utilization'] = df_filtered['production'] / df_filtered['capacity'].replace(0, np.nan)

# Calculate value metrics
df_filtered['value_per_unit'] = df_filtered['shipment_value_thousand_baht'] / df_filtered['total'].replace(0, np.nan)
df_filtered['waste_value'] = df_filtered['waste'] * df_filtered['value_per_unit']

# Handle infinite values and NaN values
df_filtered = df_filtered.replace([np.inf, -np.inf], np.nan)
df_filtered = df_filtered.fillna(0)

# -------------------- Tabs --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Waste Analysis", "Inventory Analysis", 
    "Production vs Demand", "Economic Impact"
])

# -------------------- Tab 1: Overview --------------------
with tab1:
    st.markdown('<p class="section-header">📊 Overview Metrics</p>', unsafe_allow_html=True)
    
    # Calculate metrics with error handling
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
    waste_by_product['waste_rate'] = waste_by_product['waste'] / waste_by_product['production'].replace(0, np.nan)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(waste_by_product, x='Product', y='waste', title="Total Waste by Product")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(waste_by_product, x='Product', y='waste_rate', title="Waste Rate by Product")
        st.plotly_chart(fig, use_container_width=True)

# -------------------- Tab 2: Waste Analysis --------------------
with tab2:
    st.markdown('<p class="section-header">📈 Waste Analysis</p>', unsafe_allow_html=True)
    
    # Seasonal waste patterns
    waste_by_month = df_filtered.groupby(['Month', 'Product']).agg({'waste': 'mean'}).reset_index()
    fig = px.line(waste_by_month, x='Month', y='waste', color='Product', title="Average Waste by Month")
    st.plotly_chart(fig, use_container_width=True)
    
    # Waste distribution
    fig = px.box(df_filtered, x='Product', y='waste', title="Distribution of Waste by Product")
    st.plotly_chart(fig, use_container_width=True)
    
    # Yearly comparison
    waste_by_year = df_filtered.groupby(['Year', 'Product']).agg({'waste': 'sum'}).reset_index()
    fig = px.bar(waste_by_year, x='Year', y='waste', color='Product', barmode='group', title="Total Waste by Year and Product")
    st.plotly_chart(fig, use_container_width=True)

# -------------------- Tab 3: Inventory Analysis --------------------
with tab3:
    st.markdown('<p class="section-header">📦 Inventory Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Inventory turnover
        turnover_by_product = df_filtered.groupby('Product').agg({'inventory_turnover': 'mean'}).reset_index()
        fig = px.bar(turnover_by_product, x='Product', y='inventory_turnover', title="Average Inventory Turnover")
        st.plotly_chart(fig, use_container_width=True)
        
        # Days of supply
        df_filtered['days_of_supply'] = (df_filtered['month_end_inventory'] / df_filtered['domestic'].replace(0, np.nan)) * 30
        days_supply_by_product = df_filtered.groupby('Product').agg({'days_of_supply': 'mean'}).reset_index()
        fig = px.bar(days_supply_by_product, x='Product', y='days_of_supply', title="Average Days of Supply")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Inventory vs Waste relationship
        fig = px.scatter(df_filtered, x='avg_inventory', y='waste', color='Product', 
                         trendline="ols", title="Inventory vs Waste Relationship")
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly inventory patterns
        inventory_by_month = df_filtered.groupby(['Month', 'Product']).agg({
            'begin_month_inventory': 'mean'
        }).reset_index()
        fig = px.line(inventory_by_month, x='Month', y='begin_month_inventory', color='Product',
                      title="Average Beginning Inventory by Month")
        st.plotly_chart(fig, use_container_width=True)

# -------------------- Tab 4: Production vs Demand --------------------
with tab4:
    st.markdown('<p class="section-header">⚖️ Production vs Demand Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Production vs Domestic Sales
        prod_vs_domestic = df_filtered.groupby('Product').agg({
            'production': 'sum',
            'domestic': 'sum'
        }).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=prod_vs_domestic['Product'],
            y=prod_vs_domestic['production'],
            name='Production'
        ))
        fig.add_trace(go.Bar(
            x=prod_vs_domestic['Product'],
            y=prod_vs_domestic['domestic'],
            name='Domestic Sales'
        ))
        fig.update_layout(barmode='group', title="Total Production vs Domestic Sales")
        st.plotly_chart(fig, use_container_width=True)
        
        # Capacity Utilization
        utilization_by_product = df_filtered.groupby('Product').agg({
            'capacity_utilization': 'mean'
        }).reset_index()
        fig = px.bar(utilization_by_product, x='Product', y='capacity_utilization',
                     title="Average Capacity Utilization by Product")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Production-Demand Gap
        df_filtered['production_demand_gap'] = df_filtered['production'] - df_filtered['domestic']
        gap_by_product = df_filtered.groupby('Product').agg({
            'production_demand_gap': 'mean'
        }).reset_index()
        
        fig = px.bar(gap_by_product, x='Product', y='production_demand_gap',
                     title="Average Production-Demand Gap")
        st.plotly_chart(fig, use_container_width=True)
        
        # Production vs Waste Correlation
        fig = px.scatter(df_filtered, x='production', y='waste', color='Product',
                         trendline="ols", title="Correlation Between Production Volume and Waste")
        st.plotly_chart(fig, use_container_width=True)

# -------------------- Tab 5: Economic Impact --------------------
with tab5:
    st.markdown('<p class="section-header">💰 Economic Impact Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Value of Waste by Product
        waste_value_by_product = df_filtered.groupby('Product').agg({
            'waste_value': 'sum'
        }).reset_index().sort_values('waste_value', ascending=False)
        
        fig = px.bar(waste_value_by_product, x='Product', y='waste_value',
                     title="Total Value of Waste by Product (Thousand Baht)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly Waste Value Trends
        waste_value_by_month = df_filtered.groupby(['Year', 'Month']).agg({
            'waste_value': 'sum'
        }).reset_index()
        waste_value_by_month['date'] = pd.to_datetime(waste_value_by_month['Year'].astype(str) + '-' + waste_value_by_month['Month'].astype(str))
        
        fig = px.line(waste_value_by_month, x='date', y='waste_value',
                      title="Trends in Waste Value Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Waste as Percentage of Shipment Value
        total_values = df_filtered.groupby('Product').agg({
            'shipment_value_thousand_baht': 'sum',
            'waste_value': 'sum'
        }).reset_index()
        total_values['waste_pct_of_value'] = (total_values['waste_value'] / total_values['shipment_value_thousand_baht'].replace(0, np.nan)) * 100
        
        fig = px.bar(total_values, x='Product', y='waste_pct_of_value',
                     title="Waste Value as Percentage of Total Shipment Value")
        st.plotly_chart(fig, use_container_width=True)
        
        # Seasonal Waste Cost Patterns
        waste_value_by_season = df_filtered.groupby('Month').agg({
            'waste_value': 'mean'
        }).reset_index()
        
        fig = px.line(waste_value_by_season, x='Month', y='waste_value',
                      title="Average Monthly Waste Value (Seasonal Pattern)")
        st.plotly_chart(fig, use_container_width=True)

# -------------------- Insights and Recommendations --------------------
st.markdown("---")
st.markdown('<p class="section-header">📋 Key Insights and Recommendations</p>', unsafe_allow_html=True)

if not df_filtered.empty:
    # Generate insights
    waste_by_product = df_filtered.groupby('Product').agg({
        'waste': 'sum',
        'production': 'sum'
    }).reset_index()
    waste_by_product['waste_rate'] = waste_by_product['waste'] / waste_by_product['production'].replace(0, np.nan)
    
    highest_waste_product = waste_by_product.loc[waste_by_product['waste_rate'].idxmax()]
    lowest_waste_product = waste_by_product.loc[waste_by_product['waste_rate'].idxmin()]
    
    waste_by_month = df_filtered.groupby('Month').agg({'waste': 'mean'}).reset_index()
    highest_waste_month = waste_by_month.loc[waste_by_month['waste'].idxmax()]
    
    turnover_by_product = df_filtered.groupby('Product').agg({'inventory_turnover': 'mean'}).reset_index()
    lowest_turnover = turnover_by_product.loc[turnover_by_product['inventory_turnover'].idxmin()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Key Findings")
        st.markdown(f"""
        - **{highest_waste_product['Product']}** has the highest waste rate at **{highest_waste_product['waste_rate']:.2%}**
        - **{lowest_waste_product['Product']}** has the lowest waste rate at **{lowest_waste_product['waste_rate']:.2%}**
        - Month **{int(highest_waste_month['Month'])}** typically has the highest waste levels
        - **{lowest_turnover['Product']}** has the slowest inventory turnover
        """)
    
    with col2:
        st.markdown("#### Recommendations")
        st.markdown("""
        - Implement better inventory management for low turnover products
        - Adjust production schedules based on seasonal demand patterns
        - Improve storage conditions for high-waste products
        - Develop strategies to redirect potential waste to alternative markets
        - Enhance demand forecasting to reduce production-demand mismatch
        """)

# -------------------- Download Results --------------------
st.sidebar.markdown("---")
st.sidebar.download_button(
    label="Download Analysis Results",
    data=df_filtered.to_csv(index=False),
    file_name="food_waste_analysis.csv",
    mime="text/csv"
)





