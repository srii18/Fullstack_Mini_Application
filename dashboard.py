import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Configure Streamlit page
st.set_page_config(
    page_title="Receipt Processing Dashboard",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .upload-section {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_api_connection():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200
    except:
        return False

def upload_file(file):
    """Upload file to API"""
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{API_BASE_URL}/receipts/upload", files=files)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return None

def get_receipts():
    """Get all receipts from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/receipts/")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_analytics():
    """Get analytics summary from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/receipts/analytics/summary")
        return response.json() if response.status_code == 200 else None
    except:
        return None

def search_receipts(filters):
    """Search receipts with filters"""
    try:
        response = requests.post(f"{API_BASE_URL}/receipts/search", json=filters)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def apply_manual_correction(receipt_id, correction_data):
    """Apply manual corrections to a receipt"""
    try:
        response = requests.post(f"{API_BASE_URL}/receipts/{receipt_id}/correct", json=correction_data)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Correction failed: {str(e)}")
        return None

def export_receipts(export_format, filters=None, fields=None):
    """Export receipts as CSV or JSON"""
    try:
        export_data = {
            "format": export_format,
            "filters": filters,
            "include_fields": fields
        }
        response = requests.post(f"{API_BASE_URL}/receipts/export", json=export_data)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        st.error(f"Export failed: {str(e)}")
        return None

def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<h1 class="main-header">🧾 Receipt Processing Dashboard</h1>', unsafe_allow_html=True)
    
    # Check API connection
    if not check_api_connection():
        st.error("⚠️ Backend API is not running. Please start the FastAPI server first.")
        st.code("uvicorn main:app --reload")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["📤 Upload", "📋 View Receipts", "🔍 Search", "✏️ Manual Correction", "📥 Export Data", "📊 Analytics"]
    )
    
    if page == "📤 Upload":
        upload_page()
    elif page == "📋 View Receipts":
        view_receipts_page()
    elif page == "🔍 Search":
        search_page()
    elif page == "✏️ Manual Correction":
        manual_correction_page()
    elif page == "📥 Export Data":
        export_page()
    elif page == "📊 Analytics":
        analytics_page()

def upload_page():
    """File upload page"""
    st.header("Upload Receipt")
    
    st.markdown("""
    <div class="upload-section">
        <h3>📁 Upload your receipt or bill</h3>
        <p>Supported formats: JPG, PNG, PDF, TXT</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['jpg', 'jpeg', 'png', 'pdf', 'txt'],
        help="Upload receipt images, PDFs, or text files for processing"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Filename:** {uploaded_file.name}")
        with col2:
            st.info(f"**Size:** {uploaded_file.size} bytes")
        with col3:
            st.info(f"**Type:** {uploaded_file.type}")
        
        # Upload button
        if st.button("🚀 Process Receipt", type="primary"):
            with st.spinner("Processing receipt..."):
                result = upload_file(uploaded_file)
                
                if result:
                    st.success("✅ Receipt processed successfully!")
                    
                    # Display extracted data
                    st.subheader("Extracted Information")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Vendor", result.get('vendor', 'Not detected'))
                        st.metric("Amount", f"${result.get('amount', 0):.2f}" if result.get('amount') else "Not detected")
                    
                    with col2:
                        st.metric("Category", result.get('category', 'Not categorized'))
                        if result.get('transaction_date'):
                            date_str = result['transaction_date'][:10]  # Extract date part
                            st.metric("Date", date_str)
                        else:
                            st.metric("Date", "Not detected")
                    
                    # Confidence score
                    if result.get('confidence_score'):
                        confidence = result['confidence_score'] * 100
                        st.progress(confidence / 100)
                        st.caption(f"OCR Confidence: {confidence:.1f}%")
                    
                    # Raw text (expandable)
                    if result.get('raw_text'):
                        with st.expander("View Raw Extracted Text"):
                            st.text(result['raw_text'])
                
                else:
                    st.error("❌ Failed to process receipt. Please try again.")

def view_receipts_page():
    """View all receipts page"""
    st.header("All Receipts")
    
    receipts = get_receipts()
    
    if not receipts:
        st.info("No receipts found. Upload some receipts to get started!")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(receipts)
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Receipts", len(df))
    with col2:
        processed_count = len(df[df['processing_status'] == 'processed'])
        st.metric("Processed", processed_count)
    with col3:
        total_amount = df[df['amount'].notna()]['amount'].sum()
        st.metric("Total Amount", f"${total_amount:.2f}")
    with col4:
        avg_amount = df[df['amount'].notna()]['amount'].mean()
        st.metric("Average Amount", f"${avg_amount:.2f}" if not pd.isna(avg_amount) else "$0.00")
    
    # Filter options
    st.subheader("Filter Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Status", ["All", "processed", "pending", "failed"])
    with col2:
        vendors = ["All"] + list(df[df['vendor'].notna()]['vendor'].unique())
        vendor_filter = st.selectbox("Vendor", vendors)
    with col3:
        categories = ["All"] + list(df[df['category'].notna()]['category'].unique())
        category_filter = st.selectbox("Category", categories)
    
    # Apply filters
    filtered_df = df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['processing_status'] == status_filter]
    if vendor_filter != "All":
        filtered_df = filtered_df[filtered_df['vendor'] == vendor_filter]
    if category_filter != "All":
        filtered_df = filtered_df[filtered_df['category'] == category_filter]
    
    # Display table
    st.subheader(f"Receipts ({len(filtered_df)} records)")
    
    # Select columns to display
    display_columns = ['id', 'filename', 'vendor', 'amount', 'category', 'transaction_date', 'processing_status']
    display_df = filtered_df[display_columns].copy()
    
    # Format the display
    if not display_df.empty:
        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        display_df['transaction_date'] = pd.to_datetime(display_df['transaction_date']).dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No receipts match the selected filters.")

def search_page():
    """Advanced search page"""
    st.header("Advanced Search")
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keyword = st.text_input("Keyword Search", help="Search in vendor names and text content")
            vendor = st.text_input("Vendor Name")
            category = st.text_input("Category")
        
        with col2:
            min_amount = st.number_input("Minimum Amount", min_value=0.0, value=0.0)
            max_amount = st.number_input("Maximum Amount", min_value=0.0, value=1000.0)
            
            # Date range
            col2a, col2b = st.columns(2)
            with col2a:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365))
            with col2b:
                end_date = st.date_input("End Date", value=datetime.now())
        
        # Sort options
        st.subheader("Sort Options")
        col3, col4 = st.columns(2)
        with col3:
            sort_field = st.selectbox("Sort by", ["upload_date", "transaction_date", "amount", "vendor", "category"])
        with col4:
            sort_direction = st.selectbox("Direction", ["Ascending", "Descending"])
        
        search_button = st.form_submit_button("🔍 Search", type="primary")
    
    if search_button:
        # Prepare search filters
        filters = {}
        if keyword:
            filters['keyword'] = keyword
        if vendor:
            filters['vendor'] = vendor
        if category:
            filters['category'] = category
        if min_amount > 0:
            filters['min_amount'] = min_amount
        if max_amount > 0:
            filters['max_amount'] = max_amount
        if start_date:
            filters['start_date'] = start_date.isoformat()
        if end_date:
            filters['end_date'] = end_date.isoformat()
        
        # Add sort options
        sort_options = {
            "field": sort_field,
            "direction": "desc" if sort_direction == "Descending" else "asc"
        }
        
        with st.spinner("Searching..."):
            # Make search request
            search_payload = {
                "filters": filters,
                "sort": sort_options
            }
            
            try:
                response = requests.post(f"{API_BASE_URL}/receipts/search", json=filters)
                results = response.json() if response.status_code == 200 else []
                
                st.subheader(f"Search Results ({len(results)} found)")
                
                if results:
                    # Convert to DataFrame
                    results_df = pd.DataFrame(results)
                    display_columns = ['id', 'filename', 'vendor', 'amount', 'category', 'transaction_date']
                    
                    if not results_df.empty:
                        display_df = results_df[display_columns].copy()
                        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
                        display_df['transaction_date'] = pd.to_datetime(display_df['transaction_date']).dt.strftime('%Y-%m-%d')
                        
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No results found for your search criteria.")
                    
            except Exception as e:
                st.error(f"Search failed: {str(e)}")

def manual_correction_page():
    """Manual correction page for editing receipt fields"""
    st.header("✏️ Manual Field Correction")
    
    st.markdown("""
    <div class="upload-section">
        <h3>🔧 Correct Receipt Data</h3>
        <p>Select a receipt and manually correct any parsing errors</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all receipts
    receipts = get_receipts()
    
    if not receipts:
        st.warning("No receipts found. Please upload some receipts first.")
        return
    
    # Receipt selection
    receipt_options = {f"ID {r['id']}: {r['filename']} - {r.get('vendor', 'Unknown')}": r for r in receipts}
    selected_receipt_key = st.selectbox("Select Receipt to Correct:", list(receipt_options.keys()))
    
    if selected_receipt_key:
        selected_receipt = receipt_options[selected_receipt_key]
        
        st.subheader(f"Editing Receipt: {selected_receipt['filename']}")
        
        # Display current values and correction form
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Current Values:**")
            st.info(f"**Vendor:** {selected_receipt.get('vendor', 'Not detected')}")
            st.info(f"**Amount:** ${selected_receipt.get('amount', 'Not detected')}")
            st.info(f"**Date:** {selected_receipt.get('transaction_date', 'Not detected')}")
            st.info(f"**Category:** {selected_receipt.get('category', 'Not detected')}")
            st.info(f"**Status:** {selected_receipt.get('processing_status', 'Unknown')}")
        
        with col2:
            st.markdown("**Corrections:**")
            
            # Correction form
            with st.form(f"correction_form_{selected_receipt['id']}"):
                new_vendor = st.text_input("Vendor Name:", value=selected_receipt.get('vendor', ''))
                new_amount = st.number_input("Amount:", min_value=0.0, value=float(selected_receipt.get('amount', 0) or 0), step=0.01)
                
                # Date input
                current_date = None
                if selected_receipt.get('transaction_date'):
                    try:
                        current_date = datetime.fromisoformat(selected_receipt['transaction_date'].replace('Z', '+00:00')).date()
                    except:
                        current_date = None
                
                new_date = st.date_input("Transaction Date:", value=current_date)
                
                # Category selection
                categories = ['grocery', 'dining', 'utilities', 'transportation', 'healthcare', 'retail', 'other']
                current_category = selected_receipt.get('category', 'other')
                if current_category not in categories:
                    categories.append(current_category)
                
                new_category = st.selectbox("Category:", categories, index=categories.index(current_category) if current_category in categories else 0)
                
                notes = st.text_area("Correction Notes:", placeholder="Optional notes about the corrections made...")
                
                submitted = st.form_submit_button("Apply Corrections", type="primary")
                
                if submitted:
                    correction_data = {
                        "vendor": new_vendor if new_vendor != selected_receipt.get('vendor', '') else None,
                        "amount": new_amount if new_amount != float(selected_receipt.get('amount', 0) or 0) else None,
                        "transaction_date": new_date.isoformat() if new_date != current_date else None,
                        "category": new_category if new_category != selected_receipt.get('category', '') else None,
                        "notes": notes if notes else None
                    }
                    
                    # Remove None values
                    correction_data = {k: v for k, v in correction_data.items() if v is not None}
                    
                    if correction_data:
                        result = apply_manual_correction(selected_receipt['id'], correction_data)
                        if result:
                            st.success("✅ Corrections applied successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to apply corrections. Please try again.")
                    else:
                        st.warning("No changes detected.")
        
        # Display raw text for reference
        if selected_receipt.get('raw_text'):
            with st.expander("📄 View Raw Text (for reference)"):
                st.text(selected_receipt['raw_text'])

def export_page():
    """Export data page"""
    st.header("📥 Export Receipt Data")
    
    st.markdown("""
    <div class="upload-section">
        <h3>💾 Export Your Data</h3>
        <p>Export receipt data as CSV or JSON with optional filtering</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Export format selection
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox("Export Format:", ["csv", "json"])
    
    with col2:
        # Field selection
        available_fields = ['id', 'filename', 'vendor', 'transaction_date', 'amount', 'category', 'upload_date', 'confidence_score', 'processing_status']
        selected_fields = st.multiselect("Fields to Include:", available_fields, default=['id', 'filename', 'vendor', 'transaction_date', 'amount', 'category'])
    
    # Filters section
    st.subheader("🔍 Export Filters (Optional)")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        filter_vendor = st.text_input("Vendor (contains):")
        filter_category = st.selectbox("Category:", ['', 'grocery', 'dining', 'utilities', 'transportation', 'healthcare', 'retail', 'other'])
    
    with filter_col2:
        filter_min_amount = st.number_input("Min Amount:", min_value=0.0, value=0.0, step=0.01)
        filter_max_amount = st.number_input("Max Amount:", min_value=0.0, value=10000.0, step=0.01)
    
    with filter_col3:
        filter_start_date = st.date_input("Start Date:", value=None)
        filter_end_date = st.date_input("End Date:", value=None)
    
    # Build filters
    filters = {}
    if filter_vendor:
        filters['vendor'] = filter_vendor
    if filter_category:
        filters['category'] = filter_category
    if filter_min_amount > 0:
        filters['min_amount'] = filter_min_amount
    if filter_max_amount < 10000:
        filters['max_amount'] = filter_max_amount
    if filter_start_date:
        filters['start_date'] = filter_start_date.isoformat()
    if filter_end_date:
        filters['end_date'] = filter_end_date.isoformat()
    
    # Export button
    if st.button("📥 Export Data", type="primary"):
        with st.spinner("Generating export..."):
            export_data = export_receipts(
                export_format=export_format,
                filters=filters if filters else None,
                fields=selected_fields if selected_fields else None
            )
            
            if export_data:
                filename = f"receipts_export.{export_format}"
                mime_type = "text/csv" if export_format == "csv" else "application/json"
                
                st.download_button(
                    label=f"💾 Download {export_format.upper()} File",
                    data=export_data,
                    file_name=filename,
                    mime=mime_type
                )
                st.success(f"✅ Export ready! Click the download button above to save your {export_format.upper()} file.")
            else:
                st.error("❌ Export failed. Please try again.")
    
    # Preview section
    st.subheader("👀 Data Preview")
    receipts = get_receipts()
    if receipts:
        # Apply filters for preview
        filtered_receipts = receipts
        if filters:
            # Simple client-side filtering for preview
            if 'vendor' in filters:
                filtered_receipts = [r for r in filtered_receipts if filters['vendor'].lower() in (r.get('vendor', '') or '').lower()]
            if 'category' in filters:
                filtered_receipts = [r for r in filtered_receipts if r.get('category') == filters['category']]
        
        st.info(f"Found {len(filtered_receipts)} receipts matching your criteria")
        
        if filtered_receipts:
            # Show first few records as preview
            preview_data = []
            for receipt in filtered_receipts[:5]:  # Show first 5
                row = {}
                for field in (selected_fields or available_fields):
                    row[field] = receipt.get(field, '')
                preview_data.append(row)
            
            df = pd.DataFrame(preview_data)
            st.dataframe(df, use_container_width=True)
            
            if len(filtered_receipts) > 5:
                st.info(f"Showing first 5 records. Total: {len(filtered_receipts)} records will be exported.")

def analytics_page():
    """Analytics and visualizations page"""
    st.header("📊 Analytics Dashboard")
    
    analytics = get_analytics()
    
    if not analytics:
        st.error("Unable to load analytics data. Make sure you have processed receipts.")
        return
    
    # Basic Statistics
    st.subheader("📈 Basic Statistics")
    basic_stats = analytics.get('basic_statistics', {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Receipts", basic_stats.get('total_receipts', 0))
    with col2:
        st.metric("Total Amount", f"${basic_stats.get('total_amount', 0):.2f}")
    with col3:
        st.metric("Average Amount", f"${basic_stats.get('average_amount', 0):.2f}")
    with col4:
        st.metric("Median Amount", f"${basic_stats.get('median_amount', 0):.2f}")
    
    # Vendor Analysis
    st.subheader("🏪 Top Vendors")
    top_vendors = analytics.get('top_vendors', [])
    
    if top_vendors:
        col1, col2 = st.columns(2)
        
        with col1:
            # Top vendors by amount (bar chart)
            vendor_df = pd.DataFrame(top_vendors[:10])
            fig_vendors = px.bar(
                vendor_df, 
                x='total_amount', 
                y='vendor',
                orientation='h',
                title="Top 10 Vendors by Total Spending",
                labels={'total_amount': 'Total Amount ($)', 'vendor': 'Vendor'}
            )
            fig_vendors.update_layout(height=400)
            st.plotly_chart(fig_vendors, use_container_width=True)
        
        with col2:
            # Vendor distribution (pie chart)
            vendor_dist = analytics.get('vendor_distribution', [])[:8]  # Top 8 for readability
            if vendor_dist:
                vendor_dist_df = pd.DataFrame(vendor_dist)
                fig_pie = px.pie(
                    vendor_dist_df,
                    values='count',
                    names='vendor',
                    title="Vendor Distribution (by Transaction Count)"
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
    
    # Category Analysis
    st.subheader("📂 Category Analysis")
    category_dist = analytics.get('category_distribution', [])
    
    if category_dist:
        col1, col2 = st.columns(2)
        
        with col1:
            # Category distribution (bar chart)
            cat_df = pd.DataFrame(category_dist)
            fig_cat = px.bar(
                cat_df,
                x='category',
                y='count',
                title="Spending by Category",
                labels={'count': 'Number of Transactions', 'category': 'Category'}
            )
            fig_cat.update_layout(height=400)
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            # Category pie chart
            fig_cat_pie = px.pie(
                cat_df,
                values='count',
                names='category',
                title="Category Distribution"
            )
            fig_cat_pie.update_layout(height=400)
            st.plotly_chart(fig_cat_pie, use_container_width=True)
    
    # Time Series Analysis
    st.subheader("📅 Spending Trends")
    monthly_trends = analytics.get('monthly_trends', [])
    
    if monthly_trends:
        # Monthly spending trend
        trends_df = pd.DataFrame(monthly_trends)
        trends_df['month_date'] = pd.to_datetime(trends_df['month'] + '-01')
        
        fig_trend = go.Figure()
        
        # Add total amount line
        fig_trend.add_trace(go.Scatter(
            x=trends_df['month_date'],
            y=trends_df['total_amount'],
            mode='lines+markers',
            name='Total Amount',
            line=dict(color='#1f77b4', width=3)
        ))
        
        # Add moving average if available
        if 'moving_avg_amount' in trends_df.columns:
            fig_trend.add_trace(go.Scatter(
                x=trends_df['month_date'],
                y=trends_df['moving_avg_amount'],
                mode='lines',
                name='Moving Average',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
        
        fig_trend.update_layout(
            title="Monthly Spending Trends",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            height=400
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Daily Patterns
    daily_patterns = analytics.get('daily_patterns', [])
    if daily_patterns:
        st.subheader("📊 Daily Spending Patterns")
        daily_df = pd.DataFrame(daily_patterns)
        
        fig_daily = px.bar(
            daily_df,
            x='day_of_week',
            y='total_amount',
            title="Spending by Day of Week",
            labels={'total_amount': 'Total Amount ($)', 'day_of_week': 'Day of Week'}
        )
        fig_daily.update_layout(height=400)
        st.plotly_chart(fig_daily, use_container_width=True)
    
    # Amount Distribution
    amount_histogram = analytics.get('amount_histogram', [])
    if amount_histogram:
        st.subheader("💰 Amount Distribution")
        hist_df = pd.DataFrame(amount_histogram)
        
        fig_hist = px.bar(
            hist_df,
            x='bin_center',
            y='count',
            title="Distribution of Transaction Amounts",
            labels={'bin_center': 'Amount ($)', 'count': 'Number of Transactions'}
        )
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)

if __name__ == "__main__":
    main()
