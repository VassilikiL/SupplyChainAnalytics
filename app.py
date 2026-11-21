
import streamlit as st
import pandas as pd
import plotly.express as px

from sqlalchemy import create_engine
from urllib.parse import quote_plus
from io import BytesIO


# =====================================
# 1. PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="Supply Chain Analytics",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Supply Chain Analytics Dashboard")
st.caption("Python | SQL Server | Pandas | Streamlit")


# =====================================
# PROFESSIONAL CORPORATE DESIGN - HIGH CONTRAST

st.markdown("""
<style>

/* Main application */
.stApp {
    background-color: #101C32;
    color: #FFFFFF;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* All standard text */
.stApp p,
.stApp label,
.stApp span,
.stApp li,
.stMarkdown,
.stCaption,
[data-testid="stMarkdownContainer"] p {
    color: #E2EAF4;
}

/* Captions */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
small {
    color: #DCE6F2 !important;
}

/* KPI cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1C2D49, #243B5A);
    border: 1px solid #526B8C;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p {
    color: #DCE6F2 !important;
    font-weight: 600 !important;
}

div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

div[data-testid="stMetricDelta"] {
    font-weight: 600;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #172740;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: #F1F5F9 !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid #526B8C;
    border-radius: 10px;
}

/* Inputs */
.stSelectbox label,
.stMultiSelect label,
.stDateInput label {
    color: #FFFFFF !important;
    font-weight: 600;
}

/* Messages */
[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Dividers */
hr {
    border-color: #526B8C !important;
}

/* Buttons */
.stDownloadButton button,
.stButton button {
    background-color: #2563EB;
    color: #FFFFFF !important;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}

.stDownloadButton button:hover,
.stButton button:hover {
    background-color: #1D4ED8;
    color: #FFFFFF !important;
}

/* Links */
.stApp a {
    color: #93C5FD !important;
}

</style>
""", unsafe_allow_html=True)
# =====================================
# 2. DATABASE CONNECTION
# =====================================

@st.cache_resource
def get_engine():

    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=SupplyChainAnalytics;"
        "Trusted_Connection=yes;"
    )

    connection_url = quote_plus(connection_string)

    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={connection_url}"
    )


engine = get_engine()


# =====================================
# 3. LOAD DATA
# =====================================

@st.cache_data(ttl=60)
def load_data():

    # 1. INVENTORY
    inventory = pd.read_sql("""
        SELECT
            Category,
            COUNT(*) AS Total_Products,
            SUM(StockQuantity) AS Total_Stock,
            SUM(StockQuantity * UnitPrice) AS Inventory_Value
        FROM dbo.Products
        GROUP BY Category
    """, engine)

    # 2. DETAILED SALES
    sales = pd.read_sql("""
        SELECT
            s.ProductName,
            s.SaleDate,
            s.QuantitySold,
            s.UnitPrice,
            s.QuantitySold * s.UnitPrice AS Revenue,
            COALESCE(p.Category, 'Uncategorized') AS Category
        FROM dbo.Sales s
        LEFT JOIN dbo.Products p
            ON s.ProductName = p.ProductName
    """, engine)

    sales["SaleDate"] = pd.to_datetime(
        sales["SaleDate"], errors="coerce"
    )

    # 3. SUPPLIERS
    suppliers = pd.read_sql("""
        SELECT
            s.SupplierName,
            COUNT(p.ProductID) AS Total_Products,
            COALESCE(SUM(p.StockQuantity), 0) AS Total_Stock
        FROM dbo.Suppliers s
        LEFT JOIN dbo.Products p
            ON s.SupplierID = p.SupplierID
        GROUP BY s.SupplierID, s.SupplierName
    """, engine)

    # 4. ORDERS
    orders = pd.read_sql("""
        SELECT
            OrderStatus,
            COUNT(*) AS Total_Orders,
            SUM(Quantity) AS Total_Quantity,
            SUM(Quantity * UnitPrice) AS Order_Value
        FROM dbo.Orders
        GROUP BY OrderStatus
    """, engine)

    # 5. LOW STOCK
    low_stock = pd.read_sql("""
        SELECT
            ProductID,
            ProductName,
            Category,
            StockQuantity,
            UnitPrice
        FROM dbo.Products
        WHERE StockQuantity < 20
        ORDER BY StockQuantity ASC
    """, engine)

    # 6. MONTHLY SALES
    monthly_sales = pd.read_sql("""
        SELECT
            YEAR(SaleDate) AS Sales_Year,
            MONTH(SaleDate) AS Sales_Month,
            SUM(QuantitySold) AS Total_Quantity,
            SUM(QuantitySold * UnitPrice) AS Total_Revenue
        FROM dbo.Sales
        GROUP BY
            YEAR(SaleDate),
            MONTH(SaleDate)
        ORDER BY
            Sales_Year,
            Sales_Month
    """, engine)

    return (
        inventory,
        sales,
        suppliers,
        orders,
        low_stock,
        monthly_sales
    )


# =====================================
# 4. MAIN DASHBOARD
# =====================================

try:

    (
        inventory,
        sales,
        suppliers,
        orders,
        low_stock,
        monthly_sales
    ) = load_data()

    # =================================
    # 5. SIDEBAR FILTERS
    # =================================

    st.sidebar.title("Dashboard Navigation")

    section = st.sidebar.radio(
        "Select Analysis",
        [
            "Overview",
            "Inventory",
            "Sales",
            "Suppliers",
            "Orders",
            "Business Insights"
        ]
    )

    st.sidebar.divider()

    st.sidebar.subheader("Analytics Filters")

    # CATEGORY FILTER

    categories = sorted(
        sales["Category"].dropna().unique().tolist()
    )

    selected_categories = st.sidebar.multiselect(
        "Select Categories",
        options=categories,
        default=categories
    )

    # DATE FILTER

    valid_dates = sales["SaleDate"].dropna()

    if not valid_dates.empty:

        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if len(date_range) == 2:

            start_date, end_date = date_range

        else:

            start_date, end_date = min_date, max_date

    else:

        start_date = None
        end_date = None

    # =================================
    # 6. DYNAMIC DATA FILTERING
    # =================================

    filtered_sales = sales.copy()

    filtered_inventory = inventory.copy()
    filtered_low_stock = low_stock.copy()

    if selected_categories:

        filtered_sales = filtered_sales[
            filtered_sales["Category"].isin(
                selected_categories
            )
        ]

        filtered_inventory = filtered_inventory[
            filtered_inventory["Category"].isin(
                selected_categories
            )
        ]

        filtered_low_stock = filtered_low_stock[
            filtered_low_stock["Category"].isin(
                selected_categories
            )
        ]

    else:

        filtered_sales = filtered_sales.iloc[0:0]
        filtered_inventory = filtered_inventory.iloc[0:0]
        filtered_low_stock = filtered_low_stock.iloc[0:0]

    if start_date is not None and end_date is not None:

        filtered_sales = filtered_sales[
            (filtered_sales["SaleDate"].dt.date >= start_date) &
            (filtered_sales["SaleDate"].dt.date <= end_date)
        ]

    # =================================
    # 7. KPI CALCULATIONS
    # =================================

    
    # MONTHLY REVENUE GROWTH

    monthly_revenue = (
        filtered_sales
        .dropna(subset=["SaleDate"])
        .set_index("SaleDate")
        .resample("MS")["Revenue"]
        .sum()
    )

    if len(monthly_revenue) >= 2:

        current_month_revenue = monthly_revenue.iloc[-1]
        previous_month_revenue = monthly_revenue.iloc[-2]

        if previous_month_revenue > 0:

            revenue_growth = (
                (current_month_revenue - previous_month_revenue)
                / previous_month_revenue
            ) * 100

        else:
            revenue_growth = None

    else:
        revenue_growth = None

    total_products = inventory["Total_Products"].sum()

    total_stock = inventory["Total_Stock"].sum()

    inventory_value = inventory["Inventory_Value"].sum()

    total_revenue = filtered_sales["Revenue"].sum()

    total_orders = orders["Total_Orders"].sum()

    total_suppliers = len(suppliers)

    # =================================
    # 8. OVERVIEW
    # =================================

    if section == "Overview":

        st.header("Business Overview")
        # ==========================================
        # ==========================================
        # EXECUTIVE PERFORMANCE COMPARISON
        # ==========================================

        st.divider()

        # ==========================================
        # 1. SALES PERFORMANCE
        # ==========================================

        st.subheader("Executive Sales Performance")

        current_revenue = filtered_sales["Revenue"].sum()
        current_records = len(filtered_sales)
        current_quantity = filtered_sales["QuantitySold"].sum()

        current_sales_average = (
            current_revenue / current_records
            if current_records > 0 else 0
        )

        if start_date is not None and end_date is not None:

            period_days = (end_date - start_date).days + 1

            previous_start = start_date - pd.Timedelta(days=period_days)
            previous_end = start_date - pd.Timedelta(days=1)

            comparison_sales = sales.copy()

            if selected_categories:
                comparison_sales = comparison_sales[
                    comparison_sales["Category"].isin(selected_categories)
                ]
            else:
                comparison_sales = comparison_sales.iloc[0:0]

            comparison_sales = comparison_sales[
                (comparison_sales["SaleDate"].dt.date >= previous_start) &
                (comparison_sales["SaleDate"].dt.date <= previous_end)
            ]

        else:
            comparison_sales = sales.iloc[0:0]

        previous_revenue = comparison_sales["Revenue"].sum()
        previous_records = len(comparison_sales)
        previous_quantity = comparison_sales["QuantitySold"].sum()

        previous_sales_average = (
            previous_revenue / previous_records
            if previous_records > 0 else 0
        )

        def executive_change(current, previous):

            if previous <= 0:
                return None

            return ((current - previous) / previous) * 100

        revenue_change = executive_change(
            current_revenue, previous_revenue
        )

        records_change = executive_change(
            current_records, previous_records
        )

        quantity_change = executive_change(
            current_quantity, previous_quantity
        )

        sales_average_change = executive_change(
            current_sales_average, previous_sales_average
        )

        st.caption(
            f"Sales Period: {start_date} to {end_date}"
        )

        s1, s2, s3, s4 = st.columns(4)

        s1.metric(
            "Sales Revenue",
            f"{current_revenue:,.2f}",
            delta=f"{revenue_change:+.2f}%" if revenue_change is not None else "N/A"
        )

        s2.metric(
            "Sales Records",
            f"{current_records:,}",
            delta=f"{records_change:+.2f}%" if records_change is not None else "N/A"
        )

        s3.metric(
            "Quantity Sold",
            f"{current_quantity:,.0f}",
            delta=f"{quantity_change:+.2f}%" if quantity_change is not None else "N/A"
        )

        s4.metric(
            "Average Sales Record Value",
            f"{current_sales_average:,.2f}",
            delta=f"{sales_average_change:+.2f}%" if sales_average_change is not None else "N/A"
        )

        if previous_revenue <= 0:
            st.info(
                "Previous sales period has no revenue. "
                "Revenue growth cannot be calculated."
            )

        # ==========================================
        # 2. INDEPENDENT ORDER PERFORMANCE
        # ==========================================

        st.divider()
        st.subheader("Independent Order Performance")

        order_data = pd.read_sql_query("""
            SELECT
                o.OrderID,
                o.OrderDate,
                o.Quantity,
                o.UnitPrice,
                COALESCE(p.Category, 'Uncategorized') AS Category
            FROM dbo.Orders o
            LEFT JOIN dbo.Products p
                ON o.ProductID = p.ProductID
        """, engine)

        order_data["OrderDate"] = pd.to_datetime(
            order_data["OrderDate"],
            errors="coerce"
        )

        if selected_categories:
            order_data = order_data[
                order_data["Category"].isin(selected_categories)
            ]
        else:
            order_data = order_data.iloc[0:0]

        if not order_data.empty:

            order_value = (
                order_data["Quantity"] * order_data["UnitPrice"]
            ).sum()

            unique_orders = order_data["OrderID"].nunique()

            average_order_value = (
                order_value / unique_orders
                if unique_orders > 0 else 0
            )

            first_order = order_data["OrderDate"].min().date()
            last_order = order_data["OrderDate"].max().date()

            st.caption(
                f"Independent Order Period: {first_order} to {last_order}"
            )

            o1, o2, o3, o4 = st.columns(4)

            o1.metric("Total Orders", f"{unique_orders:,}")
            o2.metric("Total Order Value", f"{order_value:,.2f}")
            o3.metric("Average Order Value", f"{average_order_value:,.2f}")
            o4.metric("Order Records", f"{len(order_data):,}")

            st.info(
                "Orders are presented independently from Sales. "
                "No unsupported cross-period comparison is performed."
            )

        else:
            st.info("No orders available for the selected categories.")

        # ==========================================
        # 3. MANAGEMENT PERFORMANCE INSIGHTS
        # ==========================================

        st.divider()
        st.subheader("Management Performance Insights")

        insight1, insight2 = st.columns(2)

        with insight1:

            if current_revenue > 0:
                st.success(
                    f"Recorded Sales Revenue: {current_revenue:,.2f}"
                )
            else:
                st.warning("No sales revenue recorded.")

        with insight2:

            if previous_revenue > 0:

                if current_revenue > previous_revenue:
                    st.success("Sales revenue increased.")

                elif current_revenue < previous_revenue:
                    st.warning("Sales revenue decreased.")

                else:
                    st.info("Sales revenue remained stable.")

            else:
                st.info(
                    "Insufficient previous-period data "
                    "for revenue growth comparison."
                )

        # ==========================================
        # END EXECUTIVE PERFORMANCE COMPARISON
        # ==========================================
        # ==========================================

        # ==========================================
        # EXECUTIVE SUMMARY DASHBOARD
        # ==========================================

        st.divider()

        st.subheader("Executive Summary")

        if not filtered_sales.empty:

            # FINANCIAL KPIs
            exec_revenue = filtered_sales["Revenue"].sum()

            # Detect available order identifier
            order_column = next(
                (c for c in ["OrderID", "OrderId", "Order_ID"]
                 if c in filtered_sales.columns),
                None
            )

            if order_column:
                exec_orders = filtered_sales[order_column].nunique()
                orders_label = "Total Orders"
            else:
                exec_orders = len(filtered_sales)
                orders_label = "Sales Records"

            exec_aov = (
                exec_revenue / exec_orders
                if exec_orders > 0 else 0
            )

            # KPI CARDS
            k1, k2, k3, k4 = st.columns(4)

            k1.metric(
                "Total Revenue",
                f"{exec_revenue:,.2f}"
            )

            k2.metric(
                orders_label,
                f"{exec_orders:,.0f}"
            )

            k3.metric(
                "Average Order Value",
                f"{exec_aov:,.2f}"
            )

            k4.metric(
                "Monthly Revenue Growth",
                f"{revenue_growth:.2f}%"
                if revenue_growth is not None else "N/A"
            )

            st.divider()

            # TOP CATEGORY
            category_totals = (
                filtered_sales.groupby("Category")["Revenue"]
                .sum()
                .sort_values(ascending=False)
            )

            if not category_totals.empty:
                top_category = category_totals.index[0]
                top_category_revenue = category_totals.iloc[0]
            else:
                top_category = "N/A"
                top_category_revenue = 0

            # TOP 5 PRODUCTS
            st.markdown("### Top 5 Revenue Products")

            top_products = (
                filtered_sales.groupby("ProductName")["Revenue"]
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .reset_index()
            )

            p1, p2 = st.columns([1.5, 1])

            with p1:
                st.dataframe(
                    top_products,
                    use_container_width=True,
                    hide_index=True
                )

            with p2:
                st.markdown("### Top 3 Categories")

                top_categories = (
                    category_totals.head(3)
                    .reset_index()
                )

                st.dataframe(
                    top_categories,
                    use_container_width=True,
                    hide_index=True
                )

            # AUTOMATIC MANAGEMENT INSIGHTS
            st.markdown("### Executive Insights")

            col_a, col_b = st.columns(2)

            with col_a:
                st.info(
                    f"Leading Category: {top_category}\n\n"
                    f"Category Revenue: {top_category_revenue:,.2f}"
                )

            with col_b:
                if revenue_growth is not None:
                    if revenue_growth > 0:
                        st.success(
                            f"Revenue is growing by {revenue_growth:.2f}%."
                        )
                    elif revenue_growth < 0:
                        st.warning(
                            f"Revenue declined by {abs(revenue_growth):.2f}%."
                        )
                    else:
                        st.info("Revenue remained stable.")
                else:
                    st.info("Insufficient monthly data for growth comparison.")

        else:
            st.info("No sales data available for the selected filters.")

        # ==========================================
        # END EXECUTIVE SUMMARY DASHBOARD
        # ==========================================


        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Products",
            f"{total_products:,.0f}"
        )

        c2.metric(
            "Total Stock",
            f"{total_stock:,.0f}"
        )

        c3.metric(
            "Inventory Value",
            f"{inventory_value:,.2f}"
        )

        c4, c5, c6 = st.columns(3)

        c4.metric(
            "Filtered Revenue",
            f"{total_revenue:,.2f}"
        )

        c5.metric(
            "Total Orders",
            f"{total_orders:,.0f}"
        )

        c6.metric(
            "Total Suppliers",
            f"{total_suppliers:,.0f}"
        )

        st.divider()

        st.subheader("Inventory Value by Category")

        if not filtered_inventory.empty:

            fig = px.bar(
                filtered_inventory,
                x="Category",
                y="Inventory_Value",
                color="Category",
                text_auto=True
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.subheader("Sales Revenue by Product")

        if not filtered_sales.empty:

            product_revenue = (
                filtered_sales.groupby("ProductName")
                .agg(
                    Total_Revenue=("Revenue", "sum")
                )
                .reset_index()
            )

            fig2 = px.bar(
                product_revenue,
                x="ProductName",
                y="Total_Revenue",
                color="ProductName"
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

        else:

            st.info("No sales data for the selected filters.")

        # MONTHLY SALES TREND

        st.subheader("Monthly Sales Trend")

        if not filtered_sales.empty:

            monthly_trend = (
                filtered_sales
                .dropna(subset=["SaleDate"])
                .set_index("SaleDate")
                .resample("MS")
                .agg(
                    Total_Revenue=("Revenue", "sum")
                )
                .reset_index()
            )

            fig3 = px.line(
                monthly_trend,
                x="SaleDate",
                y="Total_Revenue",
                markers=True,
                title="Monthly Revenue Trend"
            )

            st.plotly_chart(
                fig3,
                use_container_width=True
            )
        st.subheader("Revenue Growth Analysis")

        if revenue_growth is not None:

            st.metric(
                "Monthly Revenue Growth",
                f"{revenue_growth:+.2f}%",
                delta=f"{revenue_growth:+.2f}%"
            )

        else:

            st.info(
                "Not enough monthly sales data to calculate growth."
            )
        
        st.divider()

        st.subheader("📊 Monthly Revenue Comparison")

        if len(monthly_revenue) >= 2:

            comparison_df = monthly_revenue.reset_index()

            comparison_df.columns = [
                "Month",
                "Revenue"
            ]

            comparison_df["Month"] = (
                comparison_df["Month"].dt.strftime("%B %Y")
            )

            fig_comparison = px.bar(
                comparison_df,
                x="Month",
                y="Revenue",
                color="Month",
                text_auto=".2f",
                title="January vs February Revenue"
            )

            st.plotly_chart(
                fig_comparison,
                use_container_width=True
            )

        else:

            st.info(
                "At least two months of sales data are required."
            )

    # =================================
    # 9. INVENTORY
    # =================================

        # REVENUE CONTRIBUTION BY CATEGORY
        # =====================================

        st.divider()

        st.subheader("Revenue Contribution by Category")

        if not filtered_sales.empty:

            category_revenue = (
                filtered_sales
                .groupby("Category")["Revenue"]
                .sum()
                .reset_index()
            )

            total_category_revenue = category_revenue["Revenue"].sum()

            if total_category_revenue > 0:

                category_revenue["Contribution (%)"] = (
                    category_revenue["Revenue"]
                    / total_category_revenue
                ) * 100

                category_revenue = category_revenue.sort_values(
                    "Revenue", ascending=False
                )

                fig_category = px.pie(
                    category_revenue,
                    names="Category",
                    values="Revenue",
                    hole=0.45,
                    title="Revenue Share by Category",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )

                fig_category.update_traces(
                    textposition="inside",
                    textinfo="percent+label"
                )

                st.plotly_chart(
                    fig_category,
                    use_container_width=True
                )

                st.dataframe(
                    category_revenue,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info("No revenue available for these categories.")

        else:
            st.info("No sales data available for the selected filters.")

    elif section == "Inventory":

        st.header("Inventory Analysis")

        st.metric(
            "Total Inventory Value",
            f"{filtered_inventory['Inventory_Value'].sum():,.2f}"
        )

        st.dataframe(
            filtered_inventory,
            use_container_width=True
        )

        st.subheader("Low Stock Alerts")

        if filtered_low_stock.empty:

            st.success("No low-stock products detected.")

        else:

            st.warning(
                f"{len(filtered_low_stock)} products "
                "have stock below 20 units."
            )

            st.dataframe(
                filtered_low_stock,
                use_container_width=True
            )

    # =================================
    # 10. SALES
    # =================================

    elif section == "Sales":

        st.header("Sales Performance")

        st.metric(
            "Filtered Revenue",
            f"{total_revenue:,.2f}"
        )

        st.metric(
            "Quantity Sold",
            f"{filtered_sales['QuantitySold'].sum():,.0f}"
        )

        if not filtered_sales.empty:

            top_products = (
                filtered_sales.groupby("ProductName")
                .agg(
                    Total_Quantity_Sold=("QuantitySold", "sum"),
                    Total_Revenue=("Revenue", "sum")
                )
                .reset_index()
                .nlargest(5, "Total_Quantity_Sold")
            )

            st.subheader("Top 5 Best-Selling Products")

            st.dataframe(
                top_products,
                use_container_width=True
            )

            fig = px.bar(
                top_products,
                x="ProductName",
                y="Total_Quantity_Sold",
                color="ProductName"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.subheader("Revenue Analysis")

            revenue_by_category = (
                filtered_sales.groupby("Category")["Revenue"]
                .sum()
                .reset_index()
            )

            fig2 = px.pie(
                revenue_by_category,
                names="Category",
                values="Revenue",
                title="Revenue Share by Category"
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

            st.subheader("Detailed Sales Data")

            st.dataframe(
                filtered_sales,
                use_container_width=True
            )

        else:

            st.info("No sales data available for these filters.")

    # =================================
    # 11. SUPPLIERS
    # =================================

    elif section == "Suppliers":

        st.header("Supplier Performance")

        st.dataframe(
            suppliers,
            use_container_width=True
        )

        fig = px.bar(
            suppliers,
            x="SupplierName",
            y="Total_Stock",
            color="SupplierName"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =================================
    # 12. ORDERS
    # =================================

    elif section == "Orders":

        st.header("Order Management")

        st.dataframe(
            orders,
            use_container_width=True
        )

        fig = px.pie(
            orders,
            names="OrderStatus",
            values="Total_Orders"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =================================
    # 13. BUSINESS INSIGHTS
    # =================================

    elif section == "Business Insights":

        st.header("Business Recommendations")

        if not filtered_low_stock.empty:

            st.warning(
                f"Attention! {len(filtered_low_stock)} products "
                "have stock below 20 units."
            )

            st.dataframe(
                filtered_low_stock,
                use_container_width=True
            )

        else:

            st.success("No low-stock products detected.")

        if not filtered_sales.empty:

            best_product = (
                filtered_sales.groupby("ProductName")["QuantitySold"]
                .sum()
                .idxmax()
            )

            st.info(
                f"Top-selling product: {best_product}"
            )

            best_category = (
                filtered_sales.groupby("Category")["Revenue"]
                .sum()
                .idxmax()
            )

            st.info(
                f"Highest revenue category: {best_category}"
            )

        if not inventory.empty:

            top_category = inventory.loc[
                inventory["Inventory_Value"].idxmax(),
                "Category"
            ]

            st.info(
                f"Highest inventory investment: {top_category}"
            )

    # =================================
    # 14. EXCEL EXPORT
    # =================================

    st.divider()

    st.header("Download Business Reports")

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        filtered_inventory.to_excel(
            writer,
            sheet_name="Inventory",
            index=False
        )

        filtered_sales.to_excel(
            writer,
            sheet_name="Sales",
            index=False
        )

        suppliers.to_excel(
            writer,
            sheet_name="Suppliers",
            index=False
        )

        orders.to_excel(
            writer,
            sheet_name="Orders",
            index=False
        )

        filtered_low_stock.to_excel(
            writer,
            sheet_name="Low Stock",
            index=False
        )

        monthly_sales.to_excel(
            writer,
            sheet_name="Monthly Sales",
            index=False
        )

    st.download_button(
        label="📥 Download Supply Chain Excel Report",
        data=output.getvalue(),
        file_name="SupplyChain_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # =================================
    # 15. REFRESH
    # =================================

    if st.button("🔄 Refresh Dashboard"):

        st.cache_data.clear()
        st.rerun()

    st.caption(
        "Supply Chain Analytics | Python + SQL Server"
    )


except Exception as e:

    st.error(f"Dashboard Error: {e}")

    st.exception(e)



# =====================================
