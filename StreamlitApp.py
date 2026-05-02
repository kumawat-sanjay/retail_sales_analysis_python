import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

from src.cleaning import clean_data

# ==============================
# Page Config
# ==============================

st.set_page_config(
    page_title="Retail Sales Dashboard",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Retail Sales Dashboard")
st.caption("Business Insights • Forecasting • Performance Analytics")

# ==============================
# Paths
# ==============================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "SuperStoreOrders.csv"
OUTPUT_PATH = BASE_DIR / "outputs"

# ==============================
# Load Data
# ==============================

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = clean_data(df)
    return df

df = load_data()

# ==============================
# Sidebar Filters
# ==============================

st.sidebar.header("🔍 Filters")

min_date = df['Order Date'].min()
max_date = df['Order Date'].max()

start_date, end_date = st.sidebar.slider(
    "Select Order Date Range",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime())
)

all_categories = sorted(df['Category'].dropna().unique())
category = st.sidebar.multiselect("Category", all_categories, default=all_categories)

all_regions = sorted(df['Region'].dropna().unique())
region = st.sidebar.multiselect("Region", all_regions, default=all_regions)

# ==============================
# Apply Filters
# ==============================

filtered_df = df[
    (df['Order Date'] >= pd.to_datetime(start_date)) &
    (df['Order Date'] <= pd.to_datetime(end_date)) &
    (df['Category'].isin(category)) &
    (df['Region'].isin(region))
]

# 🔍 Product Search
search_product = st.text_input("🔍 Search Product")

if search_product:
    filtered_df = filtered_df[
        filtered_df['Product Name'].str.contains(search_product, case=False)
    ]

if filtered_df.empty:
    st.warning("No data available for selected filters")
    st.stop()

# ==============================
# Previous Period
# ==============================

def calculate_previous_period(df, start_date, end_date):
    delta = end_date - start_date
    return df[
        (df['Order Date'] >= start_date - delta) &
        (df['Order Date'] < start_date)
    ]

prev_df = calculate_previous_period(df, pd.to_datetime(start_date), pd.to_datetime(end_date))

# ==============================
# KPIs
# ==============================

def format_growth(value):
    if value > 0:
        return f"🔼 {value:.2f}%"
    elif value < 0:
        return f"🔽 {value:.2f}%"
    return "0%"

total_sales = filtered_df['Sales'].sum()
total_profit = filtered_df['Profit'].sum()
avg_discount = filtered_df['Discount'].mean()

prev_sales = prev_df['Sales'].sum()
prev_profit = prev_df['Profit'].sum()

sales_growth = ((total_sales - prev_sales) / prev_sales * 100) if prev_sales else 0
profit_growth = ((total_profit - prev_profit) / prev_profit * 100) if prev_profit else 0

profit_margin = (total_profit / total_sales) if total_sales else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Total Sales", f"{total_sales:,.0f}", format_growth(sales_growth))
col2.metric("📈 Total Profit", f"{total_profit:,.0f}", format_growth(profit_growth))
col3.metric("🎯 Avg Discount", f"{avg_discount:.2%}")
col4.metric("📊 Profit Margin", f"{profit_margin:.2%}")

st.markdown("---")

# ==============================
# Tabs
# ==============================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Sales",
    "📦 Products",
    "👥 Customers",
    "🌍 Region",
    "🔮 Forecast"
])

# ==============================
# 📊 Sales
# ==============================

with tab1:
    filtered_df['Month'] = filtered_df['Order Date'].dt.to_period('M').dt.to_timestamp()
    monthly_sales = filtered_df.groupby('Month')['Sales'].sum().reset_index()

    fig = px.line(monthly_sales, x='Month', y='Sales', title="Monthly Sales Trend")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.scatter(filtered_df, x="Discount", y="Profit",
                      title="Discount vs Profit Impact", opacity=0.6)
    st.plotly_chart(fig2, use_container_width=True)

# ==============================
# 📦 Products
# ==============================

with tab2:
    col1, col2, col3 = st.columns([2,1,1])

    with col1:
        st.subheader("Top Products")

    with col2:
        top_n = st.selectbox("Top N", [5,10,15,20], index=1, key="p_top")

    with col3:
        measure = st.selectbox("Measure", ["Sales","Profit"], key="p_measure")

    product_data = filtered_df.groupby('Product Name').agg({'Sales':'sum','Profit':'sum'}).reset_index()
    product_data = product_data.sort_values(by=measure, ascending=False).head(top_n)

    fig = px.bar(product_data, x=measure, y='Product Name', orientation='h')

    fig.update_layout(
        yaxis=dict(
            categoryorder='array',
            categoryarray=product_data['Product Name'],
            autorange="reversed"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# 👥 Customers
# ==============================

with tab3:
    col1, col2, col3 = st.columns([2,1,1])

    with col1:
        st.subheader("Top Customers")

    with col2:
        top_n = st.selectbox("Top N", [5,10,15,20], index=1, key="c_top")

    with col3:
        measure = st.selectbox("Measure", ["Sales","Profit"], key="c_measure")

    customer_data = filtered_df.groupby('Customer Name').agg({'Sales':'sum','Profit':'sum'}).reset_index()
    customer_data = customer_data.sort_values(by=measure, ascending=False).head(top_n)

    fig = px.bar(customer_data, x=measure, y='Customer Name', orientation='h')

    fig.update_layout(
        yaxis=dict(
            categoryorder='array',
            categoryarray=customer_data['Customer Name'],
            autorange="reversed"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# 🌍 Region
# ==============================

with tab4:
    measure = st.selectbox("Measure", ["Sales","Profit"], key="r_measure")

    region_data = filtered_df.groupby('Region').agg({'Sales':'sum','Profit':'sum'}).reset_index()
    region_data = region_data.sort_values(by=measure, ascending=False)

    fig = px.bar(region_data, x=measure, y='Region', orientation='h')

    fig.update_layout(
        yaxis=dict(
            categoryorder='array',
            categoryarray=region_data['Region'],
            autorange="reversed"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# 🔮 Forecast
# ==============================

with tab5:
    forecast_file = OUTPUT_PATH / "sales_forecast.csv"

    if forecast_file.exists():
        forecast_df = pd.read_csv(forecast_file)
        pred = float(forecast_df.iloc[0,0])

        fig = px.line(monthly_sales, x='Month', y='Sales', title="Sales Forecast")
        fig.add_scatter(
            x=[monthly_sales['Month'].max()],
            y=[pred],
            mode='markers',
            name='Forecast'
        )

        st.plotly_chart(fig, use_container_width=True)
        st.metric("📈 Predicted Sales", f"{pred:,.0f}")

# ==============================
# Insights
# ==============================

st.markdown("---")
st.subheader("🧠 Smart Insights")

top_region = filtered_df.groupby('Region')['Sales'].sum().idxmax()
worst_region = filtered_df.groupby('Region')['Profit'].sum().idxmin()

st.write(f"• Highest sales region: **{top_region}**")
st.write(f"• Lowest profit region: **{worst_region}**")

if avg_discount > 0.3:
    st.write("• High discounts detected → potential profit leakage")

# ==============================
# Download
# ==============================

csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button("📥 Download Filtered Data", csv, "data.csv", "text/csv")

# ==============================
# Raw Data
# ==============================

with st.expander("📊 View Raw Data"):
    st.dataframe(filtered_df)