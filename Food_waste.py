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

available_columns = df.columns.tolist()

# Identify numeric and categorical columns
numeric_cols = [col for col in available_columns if pd.api.types.is_numeric_dtype(df[col])]
categorical_cols = [col for col in available_columns if col not in numeric_cols]

st.sidebar.write("🔢 Numeric columns:", numeric_cols)
st.sidebar.write("🏷️ Categorical columns:", categorical_cols)

# Auto-detect likely columns
detected_columns = {
    'product': None,
    'year': None,
    'month': None,
    'begin_inventory': None,
    'production': None,
    'domestic': None,
    'export': None,
    'end_inventory': None
}

# Look for product column in categorical first, then numeric
for col in categorical_cols + numeric_cols:
    col_lower = col.lower()
    if not detected_columns['product'] and ('product' in col_lower or 'item' in col_lower or 'name' in col_lower):
        detected_columns['product'] = col
    elif not detected_columns['year'] and 'year' in col_lower:
        detected_columns['year'] = col
    elif not detected_columns['month'] and 'month' in col_lower:
        detected_columns['month'] = col
    elif not detected_columns['begin_inventory'] and ('begin' in col_lower or 'start' in col_lower) and ('invent' in col_lower or 'stock' in col_lower):
        detected_columns['begin_inventory'] = col
    elif not detected_columns['production'] and ('production' in col_lower or 'prod' in col_lower):
        detected_columns['production'] = col
    elif not detected_columns['domestic'] and 'domestic' in col_lower:
        detected_columns['domestic'] = col
    elif not detected_columns['export'] and 'export' in col_lower:
        detected_columns['export'] = col
    elif not detected_columns['end_inventory'] and ('end' in col_lower or 'final' in col_lower) and ('invent' in col_lower or 'stock' in col_lower):
        detected_columns['end_inventory'] = col

# Let user select each column
st.sidebar.markdown("**Select Data Columns:**")

product_column = st.sidebar.selectbox(
    "Product/Item Column", 
    options=available_columns,
    index=available_columns.index(detected_columns['product']) if detected_columns['product'] in available_columns else 0
)

# Show sample values from selected product column
product_samples = df[product_column].unique()[:5]
st.sidebar.write(f"Sample products: {', '.join(map(str, product_samples))}")

year_column = st.sidebar.selectbox(
    "Year Column", 
    options=available_columns,
    index=available_columns.index(detected_columns['year']) if detected_columns['year'] in available_columns else min(1, len(available_columns)-1)
)

month_column = st.sidebar.selectbox(
    "Month Column", 
    options=available_columns,
    index=available_columns.index(detected_columns['month']) if detected_columns['month'] in available_columns else min(2, len(available_columns)-1)
)

# Select numeric data columns
st.sidebar.markdown("**Select Numeric Data Columns:**")

begin_inv_col = st.sidebar.selectbox(
    "Begin Inventory Column", 
    options=numeric_cols,
    index=numeric_cols.index(detected_columns['begin_inventory']) if detected_columns['begin_inventory'] in numeric_cols else 0
)

production_col = st.sidebar.selectbox(
    "Production Column", 
    options=numeric_cols,
    index=numeric_cols.index(detected_columns['production']) if detected_columns['production'] in numeric_cols else min(1, len(numeric_cols)-1)
)

domestic_col = st.sidebar.selectbox(
    "Domestic Sales Column", 
    options=numeric_cols,
    index=numeric_cols.index(detected_columns['domestic']) if detected_columns['domestic'] in numeric_cols else min(2, len(numeric_cols)-1)
)

export_col = st.sidebar.selectbox(
    "Export Column", 
    options=numeric_cols,
    index=numeric_cols.index(detected_columns['export']) if detected_columns['export'] in numeric_cols else min(3, len(numeric_cols)-1)
)

end_inv_col = st.sidebar.selectbox(
    "End Inventory Column", 
    options=numeric_cols,
    index=numeric_cols.index(detected_columns['end_inventory']) if detected_columns['end_inventory'] in numeric_cols else min(4, len(numeric_cols)-1)
)

# -------------------- Analysis Parameters --------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Analysis Parameters")

# Get unique products
unique_products = df[product_column].unique()

# # Option 1: Select first 10 products
# selected_products = st.sidebar.multiselect(
#     "Select Products to Analyze",
#     options=unique_products,
#     default=unique_products[:min(10, len(unique_products))]  
# )

# Or Option 2: Select all products (might be heavy if many products)
selected_products = st.sidebar.multiselect(
    "Select Products to Analyze",
    options=unique_products,
    default=unique_products.tolist()
)

# Or Option 3: Select top 5 most common products
# product_counts = df[product_column].value_counts()
# top_products = product_counts.head(5).index.tolist()
# selected_products = st.sidebar.multiselect(
#     "Select Products to Analyze",
#     options=unique_products,
#     default=top_products
# )

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












