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
        st.write("📋 Columns in your dataset:", df.columns.tolist())
        
    else:
        st.info("Please upload your dataset to start analysis")
        st.stop()

# -------------------- Auto-detect Column Names --------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Column Mapping")

# Auto-detect potential columns
available_columns = df.columns.tolist()

# Try to automatically detect key columns
product_col = None
year_col = None
month_col = None

# Look for potential column names
for col in available_columns:
    col_lower = col.lower()
    if 'product' in col_lower or 'item' in col_lower or 'commodity' in col_lower:
        product_col = col
    elif 'year' in col_lower or 'yr' in col_lower:
        year_col = col
    elif 'month' in col_lower or 'mnth' in col_lower:
        month_col = col

# Let user confirm or select columns
if product_col:
    default_product = product_col
else:
    default_product = available_columns[0] if available_columns else None

if year_col:
    default_year = year_col
else:
    # Look for any column that might contain years
    for col in available_columns:
        if df[col].dtype in ['int64', 'float64'] and df[col].min() > 1900 and df[col].max() < 2100:
            year_col = col
            break
    default_year = year_col if year_col else available_columns[1] if len(available_columns) > 1 else None

# User selection for key columns
product_column = st.sidebar.selectbox(
    "Select Product Column",
    options=available_columns,
    index=available_columns.index(default_product) if default_product and default_product in available_columns else 0
)

year_column = st.sidebar.selectbox(
    "Select Year Column",
    options=available_columns,
    index=available_columns.index(default_year) if default_year and default_year in available_columns else min(1, len(available_columns)-1)
)

month_column = st.sidebar.selectbox(
    "Select Month Column",
    options=available_columns,
    index=available_columns.index(month_col) if month_col and month_col in available_columns else min(2, len(available_columns)-1)
)

# -------------------- Analysis Parameters --------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Analysis Parameters")

selected_products = st.sidebar.multiselect(
    "Select Products to Analyze",
    options=df[product_column].unique(),
    default=df[product_column].unique()[:3] if len(df[product_column].unique()) > 0 else []
)

# Get year range safely
try:
    year_min = int(df[year_column].min())
    year_max = int(df[year_column].max())
except:
    year_min = 2020
    year_max = 2023

year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max)
)

# -------------------- Data Cleaning --------------------
df_clean = df.copy()

# Clean numeric columns (try to clean all potential numeric columns)
numeric_columns = []
for col in df_clean.columns:
    try:
        # Try to convert to numeric
        df_clean[col] = pd.to_numeric(df_clean[col], errors='ignore')
        if df_clean[col].dtype in ['int64', 'float64']:
            numeric_columns.append(col)
    except:
        pass

st.sidebar.write("🔍 Detected numeric columns:", numeric_columns)

# -------------------- Filter Data --------------------
try:
    df_filtered = df_clean[
        (df_clean[product_column].isin(selected_products)) &
        (df_clean[year_column] >= year_range[0]) &
        (df_clean[year_column] <= year_range[1])
    ].copy()
except Exception as e:
    st.error(f"Error filtering data: {e}")
    df_filtered = df_clean.copy()

# -------------------- Derived Metrics --------------------
# Try to identify inventory and production columns automatically
inventory_cols = []
production_cols = []
sales_cols = []

for col in numeric_columns:
    col_lower = col.lower()
    if 'invent' in col_lower or 'stock' in col_lower:
        inventory_cols.append(col)
    elif 'prod' in col_lower or 'manufactur' in col_lower:
        production_cols.append(col)
    elif 'sale' in col_lower or 'domestic' in col_lower or 'export' in col_lower:
        sales_cols.append(col)

# Use the first found column for each category, or create defaults
begin_inv_col = inventory_cols[0] if inventory_cols else None
production_col = production_cols[0] if production_cols else None
domestic_col = sales_cols[0] if sales_cols else None
end_inv_col = inventory_cols[1] if len(inventory_cols) > 1 else inventory_cols[0] if inventory_cols else None

# Create default columns if missing
if begin_inv_col is None:
    df_filtered['begin_inventory'] = 100  # Default value
    begin_inv_col = 'begin_inventory'

if production_col is None:
    df_filtered['production'] = 1000  # Default value
    production_col = 'production'

if domestic_col is None:
    df_filtered['domestic_sales'] = 800  # Default value
    domestic_col = 'domestic_sales'

if end_inv_col is None:
    df_filtered['end_inventory'] = 100  # Default value
    end_inv_col = 'end_inventory'

# Calculate waste
df_filtered['waste'] = (
    df_filtered[begin_inv_col].fillna(0) + 
    df_filtered[production_col].fillna(0) - 
    df_filtered[domestic_col].fillna(0) - 
    df_filtered.get('export', pd.Series(0)).fillna(0) -  # Try to get export, default to 0
    df_filtered[end_inv_col].fillna(0)
)

# Calculate basic metrics
df_filtered['waste_rate'] = np.where(
    df_filtered[production_col] > 0,
    df_filtered['waste'] / df_filtered[production_col],
    0
)

# -------------------- Display Results --------------------
st.markdown("### 📊 Data Overview")
st.write(f"**Total records:** {len(df_filtered)}")
st.write(f"**Selected products:** {', '.join(selected_products)}")
st.write(f"**Year range:** {year_range[0]} - {year_range[1]}")

st.markdown("### 📈 Sample of Processed Data")
st.dataframe(df_filtered.head())

st.markdown("### 📋 Summary Statistics")
st.write(df_filtered[numeric_columns].describe())

# -------------------- Basic Visualizations --------------------
if len(selected_products) > 0:
    st.markdown("### 📊 Waste Analysis by Product")
    
    waste_by_product = df_filtered.groupby(product_column).agg({
        'waste': 'sum',
        production_col: 'sum'
    }).reset_index()
    
    waste_by_product['waste_rate'] = np.where(
        waste_by_product[production_col] > 0,
        waste_by_product['waste'] / waste_by_product[production_col],
        0
    )
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(waste_by_product, x=product_column, y='waste', 
                     title="Total Waste by Product")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(waste_by_product, x=product_column, y='waste_rate',
                     title="Waste Rate by Product")
        st.plotly_chart(fig, use_container_width=True)

# -------------------- Time Series Analysis --------------------
if year_column in df_filtered.columns and month_column in df_filtered.columns:
    st.markdown("### 📅 Waste Trends Over Time")
    
    waste_by_time = df_filtered.groupby([year_column, month_column]).agg({'waste': 'sum'}).reset_index()
    
    # Try to create a date column
    try:
        waste_by_time['date'] = pd.to_datetime(
            waste_by_time[year_column].astype(str) + '-' + 
            waste_by_time[month_column].astype(str)
        )
        fig = px.line(waste_by_time, x='date', y='waste', title="Total Waste Over Time")
        st.plotly_chart(fig, use_container_width=True)
    except:
        fig = px.line(waste_by_time, x=year_column, y='waste', color=month_column,
                      title="Waste by Year and Month")
        st.plotly_chart(fig, use_container_width=True)

# -------------------- Download Results --------------------
st.sidebar.markdown("---")
csv_data = df_filtered.to_csv(index=False)
st.sidebar.download_button(
    label="Download Analysis Results",
    data=csv_data,
    file_name="food_waste_analysis.csv",
    mime="text/csv"
)

# -------------------- Debug Information --------------------
with st.expander("Debug Information"):
    st.write("Original columns:", available_columns)
    st.write("Product column selected:", product_column)
    st.write("Year column selected:", year_column)
    st.write("Month column selected:", month_column)
    st.write("Numeric columns detected:", numeric_columns)
    st.write("Inventory columns found:", inventory_cols)
    st.write("Production columns found:", production_cols)
    st.write("Sales columns found:", sales_cols)









