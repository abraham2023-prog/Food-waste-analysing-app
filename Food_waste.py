import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="Food Production & Inventory Analysis Dashboard",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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

# App title
st.markdown('<p class="main-header">🍎 Food Production & Inventory Analysis Dashboard</p>', unsafe_allow_html=True)
st.markdown("Analyze food production, inventory, and shipment patterns")

# Load data
with st.sidebar:
    st.header("Data Configuration")

    st.subheader("Upload Data")
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, thousands=',')
        st.success("Data uploaded successfully!")
    else:
        st.error("Please upload a CSV file to proceed")
        st.stop()

    # Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('\n', '_')
    
    # Rename columns for consistency
    df = df.rename(columns={
        'begin_month_inventory': 'begin_inventory',
        'month-end_inventory': 'end_inventory',
        'shipment_value_(thousand_baht)': 'shipment_value'
    })
    
    st.subheader("Analysis Parameters")
    selected_products = st.multiselect(
        "Select Products to Analyze",
        options=df['product'].unique(),
        default=df['product'].unique()[:3]
    )

    year_range = st.slider(
        "Select Year Range",
        min_value=int(df['year'].min()),
        max_value=int(df['year'].max()),
        value=(int(df['year'].min()), int(df['year'].max()))
    )

    st.subheader("Waste Calculation")
    st.info("Waste = (Begin Inventory + Production) - (Domestic + Export + End Inventory)")

# Filter data based on selections
df_filtered = df[
    (df['product'].isin(selected_products)) &
    (df['year'] >= year_range[0]) &
    (df['year'] <= year_range[1])
]

# Calculate waste metrics
df_filtered['waste'] = (df_filtered['begin_inventory'] + df_filtered['production']) - (df_filtered['domestic'] + df_filtered['export'] + df_filtered['end_inventory'])
df_filtered['waste_rate'] = df_filtered['waste'] / df_filtered['production']
df_filtered['avg_inventory'] = (df_filtered['begin_inventory'] + df_filtered['end_inventory']) / 2
df_filtered['inventory_turnover'] = df_filtered['domestic'] / df_filtered['avg_inventory']
df_filtered['capacity_utilization'] = df_filtered['production'] / df_filtered['capacity']
df_filtered['value_per_unit'] = df_filtered['shipment_value'] / df_filtered['total']
df_filtered['waste_value'] = df_filtered['waste'] * df_filtered['value_per_unit']

# Create tabs for different analyses
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Waste Analysis",
    "Inventory Analysis",
    "Production vs Demand",
    "Economic Impact"
])

with tab1:
    st.markdown('<p class="section-header">📊 Overview Metrics</p>', unsafe_allow_html=True)

    # Calculate overall metrics
    total_waste = df_filtered['waste'].sum()
    total_production = df_filtered['production'].sum()
    overall_waste_rate = total_waste / total_production if total_production > 0 else 0
    total_waste_value = df_filtered['waste_value'].sum()
    avg_turnover = df_filtered['inventory_turnover'].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Waste", f"{total_waste:,.0f} tons")
    with col2:
        st.metric("Overall Waste Rate", f"{overall_waste_rate:.2%}")
    with col3:
        st.metric("Value of Waste", f"฿{total_waste_value:,.0f}K")
    with col4:
        st.metric("Avg Inventory Turnover", f"{avg_turnover:.2f}")

    # Time series of waste
    st.markdown("#### Waste Trends Over Time")
    waste_by_time = df_filtered.groupby(['year', 'month']).agg({'waste': 'sum'}).reset_index()
    waste_by_time['date'] = pd.to_datetime(waste_by_time['year'].astype(str) + '-' + waste_by_time['month'].astype(str))

    fig = px.line(waste_by_time, x='date', y='waste',
                  title="Total Waste Over Time")
    st.plotly_chart(fig, use_container_width=True)

    # Waste by product
    st.markdown("#### Waste by Product")
    waste_by_product = df_filtered.groupby('product').agg({
        'waste': 'sum',
        'production': 'sum',
        'waste_value': 'sum'
    }).reset_index()
    waste_by_product['waste_rate'] = waste_by_product['waste'] / waste_by_product['production']

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(waste_by_product, x='product', y='waste',
                     title="Total Waste by Product")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(waste_by_product, x='product', y='waste_rate',
                     title="Waste Rate by Product")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown('<p class="section-header">📈 Waste Analysis</p>', unsafe_allow_html=True)

    # Seasonal waste patterns
    st.markdown("#### Seasonal Waste Patterns")
    waste_by_month = df_filtered.groupby(['month', 'product']).agg({'waste': 'mean'}).reset_index()

    fig = px.line(waste_by_month, x='month', y='waste', color='product',
                  title="Average Waste by Month")
    st.plotly_chart(fig, use_container_width=True)

    # Waste distribution
    st.markdown("#### Waste Distribution by Product")
    fig = px.box(df_filtered, x='product', y='waste',
                 title="Distribution of Waste Amounts by Product")
    st.plotly_chart(fig, use_container_width=True)

    # Yearly comparison
    st.markdown("#### Yearly Waste Comparison")
    waste_by_year = df_filtered.groupby(['year', 'product']).agg({'waste': 'sum'}).reset_index()

    fig = px.bar(waste_by_year, x='year', y='waste', color='product',
                 barmode='group', title="Total Waste by Year and Product")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown('<p class="section-header">📦 Inventory Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Inventory Turnover by Product")
        turnover_by_product = df_filtered.groupby('product').agg({
            'inventory_turnover': 'mean'
        }).reset_index().sort_values('inventory_turnover', ascending=False)

        fig = px.bar(turnover_by_product, x='product', y='inventory_turnover',
                     title="Average Inventory Turnover Ratio")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Days of Supply")
        df_filtered['days_of_supply'] = (df_filtered['end_inventory'] / df_filtered['domestic']) * 30
        days_supply_by_product = df_filtered.groupby('product').agg({
            'days_of_supply': 'mean'
        }).reset_index().sort_values('days_of_supply', ascending=False)

        fig = px.bar(days_supply_by_product, x='product', y='days_of_supply',
                     title="Average Days of Supply")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Inventory vs Waste Relationship")
        fig = px.scatter(df_filtered, x='avg_inventory', y='waste', color='product',
                         trendline="ols", title="Relationship Between Inventory Levels and Waste")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Monthly Inventory Patterns")
        inventory_by_month = df_filtered.groupby(['month', 'product']).agg({
            'begin_inventory': 'mean',
            'end_inventory': 'mean'
        }).reset_index()

        fig = px.line(inventory_by_month, x='month', y='begin_inventory', color='product',
                      title="Average Beginning Inventory by Month")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown('<p class="section-header">⚖️ Production vs Demand Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Production vs Domestic Sales")
        prod_vs_domestic = df_filtered.groupby('product').agg({
            'production': 'sum',
            'domestic': 'sum'
        }).reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=prod_vs_domestic['product'],
            y=prod_vs_domestic['production'],
            name='Production'
        ))
        fig.add_trace(go.Bar(
            x=prod_vs_domestic['product'],
            y=prod_vs_domestic['domestic'],
            name='Domestic Sales'
        ))
        fig.update_layout(barmode='group', title="Total Production vs Domestic Sales")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Capacity Utilization")
        utilization_by_product = df_filtered.groupby('product').agg({
            'capacity_utilization': 'mean'
        }).reset_index()

        fig = px.bar(utilization_by_product, x='product', y='capacity_utilization',
                     title="Average Capacity Utilization by Product")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Production-Demand Mismatch")
        df_filtered['production_demand_gap'] = df_filtered['production'] - df_filtered['domestic']

        gap_by_product = df_filtered.groupby('product').agg({
            'production_demand_gap': 'mean'
        }).reset_index()

        fig = px.bar(gap_by_product, x='product', y='production_demand_gap',
                     title="Average Production-Demand Gap")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Production vs Waste Correlation")
        fig = px.scatter(df_filtered, x='production', y='waste', color='product',
                         trendline="ols", title="Correlation Between Production Volume and Waste")
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.markdown('<p class="section-header">💰 Economic Impact Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Value of Waste by Product")
        waste_value_by_product = df_filtered.groupby('product').agg({
            'waste_value': 'sum'
        }).reset_index().sort_values('waste_value', ascending=False)

        fig = px.bar(waste_value_by_product, x='product', y='waste_value',
                     title="Total Value of Waste by Product (Thousand Baht)")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Monthly Waste Value Trends")
        waste_value_by_month = df_filtered.groupby(['year', 'month']).agg({
            'waste_value': 'sum'
        }).reset_index()
        waste_value_by_month['date'] = pd.to_datetime(waste_value_by_month['year'].astype(str) + '-' + waste_value_by_month['month'].astype(str))

        fig = px.line(waste_value_by_month, x='date', y='waste_value',
                      title="Trends in Waste Value Over Time")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Waste as Percentage of Shipment Value")
        total_values = df_filtered.groupby('product').agg({
            'shipment_value': 'sum',
            'waste_value': 'sum'
        }).reset_index()
        total_values['waste_pct_of_value'] = total_values['waste_value'] / total_values['shipment_value'] * 100

        fig = px.bar(total_values, x='product', y='waste_pct_of_value',
                     title="Waste Value as Percentage of Total Shipment Value")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Cost of Waste by Season")
        waste_value_by_season = df_filtered.groupby('month').agg({
            'waste_value': 'mean'
        }).reset_index()

        fig = px.line(waste_value_by_season, x='month', y='waste_value',
                      title="Average Monthly Waste Value (Seasonal Pattern)")
        st.plotly_chart(fig, use_container_width=True)

# Add summary and recommendations
st.markdown("---")
st.markdown('<p class="section-header">📋 Key Insights and Recommendations</p>', unsafe_allow_html=True)

# Generate insights based on data
if not df_filtered.empty:
    # Find product with highest waste rate
    waste_by_product = df_filtered.groupby('product').agg({
        'waste': 'sum',
        'production': 'sum'
    }).reset_index()
    waste_by_product['waste_rate'] = waste_by_product['waste'] / waste_by_product['production']

    highest_waste_product = waste_by_product.loc[waste_by_product['waste_rate'].idxmax()]
    lowest_waste_product = waste_by_product.loc[waste_by_product['waste_rate'].idxmin()]

    # Find month with highest waste
    waste_by_month = df_filtered.groupby('month').agg({'waste': 'mean'}).reset_index()
    highest_waste_month = waste_by_month.loc[waste_by_month['waste'].idxmax()]

    # Inventory turnover analysis
    turnover_by_product = df_filtered.groupby('product').agg({'inventory_turnover': 'mean'}).reset_index()
    lowest_turnover = turnover_by_product.loc[turnover_by_product['inventory_turnover'].idxmin()]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Key Findings")
        st.markdown(f"""
        - **{highest_waste_product['product']}** has the highest waste rate at **{highest_waste_product['waste_rate']:.2%}**
        - **{lowest_waste_product['product']}** has the lowest waste rate at **{lowest_waste_product['waste_rate']:.2%}**
        - Month **{int(highest_waste_month['month'])}** typically has the highest waste levels
        - **{lowest_turnover['product']}** has the slowest inventory turnover
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

# Data download option
st.sidebar.markdown("---")
st.sidebar.markdown("### Download Results")
st.sidebar.download_button(
    label="Download Analysis Results",
    data=df_filtered.to_csv(index=False),
    file_name="food_production_analysis.csv",
    mime="text/csv"
)













