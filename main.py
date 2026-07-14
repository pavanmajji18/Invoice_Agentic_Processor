"""
Streamlit UI for Agentic Invoice Processing (OpenAI & LangGraph powered)
"""
import streamlit as st
import os
import json
from pathlib import Path
from PIL import Image
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from agents.invoice_agent import InvoiceProcessingAgent
from utils.ocr import OCRReader
from utils.database import InvoiceDB

# Load local environment variables
load_dotenv()

# Page configuration - Force light theme with rich styling options
st.set_page_config(
    page_title="🤖 Agentic Invoice Processor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design & Text Visibility (Force Light Mode)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Force light theme globally */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #f7fafc !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: #2d3748 !important;
    }
    
    /* Main header styling with premium gradient and soft animation */
    .main-header {
        font-size: 2.85rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -0.03em;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }
    
    /* Override dark theme texts and force dark grey/black for high readability */
    .stText, .stMarkdown, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #2d3748 !important;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    
    /* Metric Cards */
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #718096 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #1a202c !important;
        font-weight: 800 !important;
        font-size: 1.6rem !important;
    }
    
    /* OCR and Cleaned text display boxes */
    .text-display-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.25rem;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13.5px;
        line-height: 1.6;
        color: #1a202c !important;
        max-height: 350px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    
    .ocr-text-box {
        border-left: 4px solid #3b82f6;
    }
    
    .cleaned-text-box {
        border-left: 4px solid #10b981;
    }
    
    /* Processing Steps Indicator */
    .processing-step {
        background-color: #ffffff;
        border: 1px solid #edf2f7;
        padding: 0.85rem 1.25rem;
        margin: 0.4rem 0;
        border-radius: 10px;
        font-size: 15px;
        font-weight: 500;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
    }
    
    /* Sidebar Improvements */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #2d3748 !important;
    }
    
    .sidebar-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1a202c !important;
        margin-bottom: 1rem;
    }
    
    /* Tab Navigation Style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(226, 232, 240, 0.3);
        padding: 6px 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre;
        background-color: transparent;
        border-radius: 8px;
        color: #4a5568 !important;
        font-weight: 600;
        border: none;
        padding: 0px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        color: #4f46e5 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)


def check_password() -> bool:
    """Validate optional APP_PASSWORD to prevent token abuse"""
    password = os.getenv("APP_PASSWORD")
    if not password:
        try:
            if "APP_PASSWORD" in st.secrets:
                password = st.secrets["APP_PASSWORD"]
        except Exception:
            pass
        
    if not password:
        # Password check skipped if key not configured
        return True

    def password_entered():
        if st.session_state["password_input"] == password:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Render a sleek centered lock card
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="glass-card" style="text-align: center; margin-top: 4rem;">
                <div style="font-size: 3.5rem; margin-bottom: 1rem;">🔐</div>
                <h3 style="margin-bottom: 0.5rem; font-weight: 700;">Secure Portal Access</h3>
                <p style="color: #718096; font-size: 0.95rem; margin-bottom: 1.5rem;">
                    Please enter the access password to view and process invoices.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.text_input("Enter Workspace Password", type="password", on_change=password_entered, key="password_input")
        return False
        
    if not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="glass-card" style="text-align: center; margin-top: 4rem;">
                <div style="font-size: 3.5rem; margin-bottom: 1rem;">🔐</div>
                <h3 style="margin-bottom: 0.5rem; font-weight: 700;">Secure Portal Access</h3>
                <p style="color: #718096; font-size: 0.95rem; margin-bottom: 1.5rem;">
                    Please enter the access password to view and process invoices.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.text_input("Enter Workspace Password", type="password", on_change=password_entered, key="password_input")
            st.error("😕 Password incorrect. Please try again.")
        return False
        
    return True


# Run security check first
if check_password():
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        try:
            if "OPENAI_API_KEY" in st.secrets:
                openai_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass

    # Render Sidebar Configuration
    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙️ Configuration</div>', unsafe_allow_html=True)
        
        # If API key is not configured in env/secrets, render input box
        if not openai_key:
            st.warning("⚠️ OPENAI_API_KEY not found in environment or secrets!")
            openai_key = st.text_input("Configure OPENAI_API_KEY", type="password", help="Enter your OpenAI API Key")
            if not openai_key:
                st.info("👈 Please enter your OPENAI_API_KEY in the sidebar to proceed.")
                st.stop()
                
        # Model Selection
        model = st.selectbox(
            "AI Agent Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            index=0
        )
        
        # Lazy initialization or re-initialization if model changes
        if "agent" not in st.session_state or st.session_state.get("current_model") != model or st.session_state.get("current_key") != openai_key:
            st.session_state.agent = InvoiceProcessingAgent(model_name=model, api_key=openai_key)
            st.session_state.current_model = model
            st.session_state.current_key = openai_key
            
        if "ocr_reader" not in st.session_state:
            st.session_state.ocr_reader = OCRReader()
            
        if "db" not in st.session_state:
            st.session_state.db = InvoiceDB()
            
        if "processing_history" not in st.session_state:
            st.session_state.processing_history = []

        st.divider()
        
        # Sidebar Statistics Dashboard
        st.markdown('<div class="sidebar-header">📊 Stats Overview</div>', unsafe_allow_html=True)
        try:
            stats = st.session_state.db.get_stats()
            st.metric("Total Invoices", stats["total_invoices"])
            st.metric("Valid Invoices", stats["valid_invoices"])
            if stats["total_amount"] > 0:
                st.metric("Total Amount", f"${stats['total_amount']:,.2f}")
                st.metric("Average Invoice", f"${stats['average_amount']:,.2f}")
        except Exception as e:
            st.caption("No stats available yet.")


    def process_invoice(uploaded_file) -> dict:
        """Process local uploaded file using OCR and Agentic Pipeline"""
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            # Step 1: OCR Text Extraction
            with st.spinner("🔍 Step 1/3: Reading invoice using OCR..."):
                ocr_text = st.session_state.ocr_reader.read_text(temp_path)
            
            # Step 2: Agentic Processing (Clean & Extract)
            with st.spinner("🤖 Step 2/3: Processing with AI agents..."):
                result = st.session_state.agent.process(
                    file_name=uploaded_file.name,
                    ocr_text=ocr_text
                )
            
            # Step 3: SQLite Storage
            with st.spinner("💾 Step 3/3: Storing record in database..."):
                row_id = st.session_state.db.insert_invoice(
                    file_name=uploaded_file.name,
                    data=result["extracted_data"],
                    raw_json=result,
                    validation_status=result["validation_status"],
                    errors=result.get("errors", [])
                )
                result["db_id"] = row_id
            
            return result
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)


    # Main UI Header
    st.markdown('<h1 class="main-header">🤖 Agentic Invoice Processor</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI-powered invoice cleaning, extraction, and validation using LangGraph and OpenAI</div>', unsafe_allow_html=True)
    
    # Navigation Tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📋 View Database", "📊 Analytics Hub"])
    
    with tab1:
        st.markdown('<h3 style="font-weight: 700; margin-bottom: 0.5rem;">📤 Process New Invoice</h3>', unsafe_allow_html=True)
        st.markdown("Upload a PNG, JPG, or JPEG image of an invoice to run the AI agent workflow.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose an invoice image",
                type=["png", "jpg", "jpeg"],
                help="Upload an invoice image to process. Supported formats: PNG, JPG, JPEG"
            )
            
            if uploaded_file is not None:
                st.info(f"📄 **Selected File:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
                if st.button("🚀 Run Agentic Pipeline", use_container_width=True):
                    result = process_invoice(uploaded_file)
                    st.session_state.processing_history.append(result)
                    st.success("✅ **Invoice processed successfully!**")
                    st.balloons()
        
        with col2:
            if uploaded_file is not None:
                st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
            else:
                st.markdown("""
                <div style="border: 2px dashed #cbd5e0; border-radius: 12px; height: 200px; display: flex; align-items: center; justify-content: center; color: #718096; font-size: 0.95rem;">
                    Upload an invoice file to view details
                </div>
                """, unsafe_allow_html=True)
                
        # If result is processed, show detailed panel
        if st.session_state.processing_history:
            latest_result = st.session_state.processing_history[-1]
            st.divider()
            st.markdown('<h3 style="font-weight: 700;">📄 Processing Results</h3>', unsafe_allow_html=True)
            
            # Metrics
            data = latest_result["extracted_data"]
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("Vendor", data.get("vendor") or "Unknown")
            with m_col2:
                st.metric("Invoice #", data.get("number") or "N/A")
            with m_col3:
                st.metric("Date", data.get("date") or "N/A")
            with m_col4:
                total_val = data.get("total")
                curr = data.get("currency") or "USD"
                st.metric("Total Amount", f"{curr} {total_val:,.2f}" if total_val is not None else "N/A")
            
            # Line items table
            if data.get("line_items"):
                st.markdown('<h4 style="font-weight: 700; margin-top: 1rem;">📦 Extracted Line Items</h4>', unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(data["line_items"]), use_container_width=True, hide_index=True)
                
            # Pipeline nodes
            st.markdown('<h4 style="font-weight: 700; margin-top: 1rem;">🔄 Node Processing Summary</h4>', unsafe_allow_html=True)
            
            errs_str = " ".join(latest_result.get("errors", []))
            clean_success = "Clean error" not in errs_str
            extract_success = "Extract error" not in errs_str
            
            steps = [
                ("OCR Text Extraction", "✅", "Extracted text raw OCR symbols"),
                ("Clean OCR Node", "✅ AI Cleaned" if clean_success else "❌ Failed", "Corrected characters and table structure using LLM"),
                ("Extract JSON Node", "✅ AI Extracted" if extract_success else "❌ Failed", "Parsed fields into strict JSON schema using LLM"),
                ("Schema Validation Node", "✅ Passed" if latest_result["validation_status"] == "valid" else "⚠️ Warnings", "Validated numeric values and key completeness")
            ]
            
            for step_name, status, desc in steps:
                bg_color = "#f0fdf4" if "✅" in status else "#fffbeb"
                border_color = "#10b981" if "✅" in status else "#f59e0b"
                st.markdown(f"""
                <div style="background-color: {bg_color}; border-left: 4px solid {border_color}; border-radius: 8px; padding: 0.75rem 1.25rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #2d3748;">{step_name}</strong> - <span style="font-size: 0.9rem; color: #4a5568;">{desc}</span>
                    </div>
                    <span style="font-weight: 600; color: {border_color};">{status}</span>
                </div>
                """, unsafe_allow_html=True)
                
            # Warnings/Errors Box
            if latest_result.get("errors"):
                st.markdown('<h4 style="font-weight: 700; margin-top: 1.2rem;">⚠️ Validation Warnings / Errors</h4>', unsafe_allow_html=True)
                for err in latest_result["errors"]:
                    st.warning(f"• {err}")
                    
            # Expanders
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                with st.expander("🔍 View Raw OCR Text"):
                    st.markdown(f'<div class="text-display-box ocr-text-box">{latest_result["ocr_text"]}</div>', unsafe_allow_html=True)
            with exp_col2:
                with st.expander("📝 View AI Cleaned Text"):
                    st.markdown(f'<div class="text-display-box cleaned-text-box">{latest_result["clean_text"]}</div>', unsafe_allow_html=True)
                    
            with st.expander("📊 View Extracted JSON Schema"):
                st.json(data)
                
            with st.expander("🔧 View Full Processing State"):
                st.json(latest_result)
                
    with tab2:
        st.markdown('<h3 style="font-weight: 700;">📋 Processed Invoices Database</h3>', unsafe_allow_html=True)
        
        # Refresh button
        if st.button("🔄 Refresh Database View"):
            st.rerun()
            
        invoices = st.session_state.db.get_all_invoices(limit=100)
        
        if invoices:
            df = pd.DataFrame(invoices)
            
            # Format display dataframe
            disp_df = df[["id", "file_name", "vendor", "number", "date", "total", "currency", "validation_status", "created_at"]].copy()
            disp_df.columns = ["ID", "File Name", "Vendor", "Invoice #", "Date", "Total", "Currency", "Status", "Timestamp"]
            disp_df["Timestamp"] = pd.to_datetime(disp_df["Timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
            disp_df["Status"] = disp_df["Status"].apply(lambda s: "✅ Valid" if s == "valid" else "⚠️ Warnings")
            
            st.dataframe(disp_df, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Detailed row viewer
            st.markdown('<h4 style="font-weight: 700;">🔍 Detailed Record Inspector</h4>', unsafe_allow_html=True)
            selected_id = st.selectbox(
                "Select Invoice ID to view",
                options=df["id"].tolist(),
                format_func=lambda x: f"Record ID #{x} - {df[df['id'] == x]['file_name'].values[0]}"
            )
            
            if selected_id:
                inv = st.session_state.db.get_invoice_by_id(selected_id)
                if inv:
                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        st.markdown("**Core Fields:**")
                        fields_dict = {
                            "vendor": inv.get("vendor"),
                            "number": inv.get("number"),
                            "date": inv.get("date"),
                            "total": inv.get("total"),
                            "currency": inv.get("currency")
                        }
                        st.json(fields_dict)
                    with d_col2:
                        st.markdown("**Issues & Warnings:**")
                        errs = json.loads(inv.get("errors", "[]"))
                        if errs:
                            for e in errs:
                                st.warning(f"• {e}")
                        else:
                            st.success("✅ Clean record with zero schema warnings.")
                            
                    with st.expander("📄 View Full Raw JSON Payload"):
                        try:
                            st.json(json.loads(inv.get("raw_json")))
                        except:
                            st.text(inv.get("raw_json"))
                            
                    if st.button("🗑️ Delete Invoice Record", key=f"del_{selected_id}"):
                        if st.session_state.db.delete_invoice(selected_id):
                            st.success(f"Deleted invoice record #{selected_id} successfully!")
                            st.rerun()
        else:
            st.info("No records found in database. Upload and process a new invoice first!")
            
    with tab3:
        st.markdown('<h3 style="font-weight: 700;">📊 Analytics Hub</h3>', unsafe_allow_html=True)
        in_analytics = st.session_state.db.get_all_invoices(limit=1000)
        
        if in_analytics:
            adf = pd.DataFrame(in_analytics)
            
            # Key statistics row
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            with s_col1:
                st.metric("Processed Count", len(adf))
            with s_col2:
                v_ct = len(adf[adf["validation_status"] == "valid"])
                st.metric("Clean Records", v_ct)
            with s_col3:
                tot_sum = adf["total"].sum() if "total" in adf.columns else 0
                st.metric("Cumulative Sum", f"${tot_sum:,.2f}" if tot_sum > 0 else "N/A")
            with s_col4:
                avg_val = adf["total"].mean() if "total" in adf.columns and len(adf) > 0 else 0
                st.metric("Mean Value", f"${avg_val:,.2f}" if avg_val > 0 else "N/A")
                
            st.divider()
            
            # Chart layouts
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.markdown('<h5 style="font-weight: 700; text-align: center;">Invoices by Validation Status</h5>', unsafe_allow_html=True)
                st.bar_chart(adf["validation_status"].value_counts())
            with c_col2:
                st.markdown('<h5 style="font-weight: 700; text-align: center;">Top Vendors by Invoice Count</h5>', unsafe_allow_html=True)
                if "vendor" in adf.columns:
                    st.bar_chart(adf["vendor"].value_counts().head(5))
                    
            st.markdown('<h5 style="font-weight: 700; text-align: center; margin-top: 1.5rem;">Total Volume by Currency</h5>', unsafe_allow_html=True)
            if "currency" in adf.columns and "total" in adf.columns:
                curr_totals = adf.groupby("currency")["total"].sum()
                st.bar_chart(curr_totals)
        else:
            st.info("Insufficient records in SQLite to render dashboard charts.")
