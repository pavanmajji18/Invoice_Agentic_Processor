# 🏗️ Project Architecture & Setup Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Environment Setup](#environment-setup)
6. [How to Run](#how-to-run)
7. [Project Structure](#project-structure)

---

## 🎯 Project Overview

**Agentic Invoice Processor** is an AI-powered system that automatically extracts structured data from invoice images using a multi-agent architecture built with LangGraph. The system combines OCR (Optical Character Recognition) with AI agents to clean, extract, validate, and store invoice information.

### Key Features
- 🤖 **Pure Agentic Architecture** using LangGraph
- 🔍 **OCR Text Extraction** using EasyOCR
- 🧠 **AI-Powered Processing** using OpenAI GPT models
- ✅ **Automatic Validation** of extracted data
- 💾 **Persistent Storage** with SQLite
- 📊 **Analytics Dashboard** with visualizations
- 🎨 **Beautiful UI** with Streamlit

---

## 🏛️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                        │
│  (app.py) - User Interface, File Upload, Visualization      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                       │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│  │   OCR     │───▶│  Agentic │───▶│ Database │            │
│  │  Reader   │    │  Agent   │    │  Layer   │            │
│  └──────────┘    └──────────┘    └──────────┘            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Agentic Workflow (LangGraph)

```
┌─────────────┐
│  OCR Text   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Clean OCR Node │  ← AI Agent: Fixes OCR errors
└──────┬──────────┘
       │
       ▼
┌──────────────────┐
│ Extract Data Node│  ← AI Agent: Extracts structured JSON
└──────┬───────────┘
       │
       ▼
┌─────────────────┐
│ Validate Node   │  ← Validates data completeness
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Format Output   │  ← Prepares final result
└─────────────────┘
```

---

## 🔧 Component Details

### 1. **UI Layer** (`app.py`)

**Technology:** Streamlit

**Responsibilities:**
- File upload interface
- Real-time processing feedback
- Results visualization
- Invoice browsing and management
- Analytics dashboard

**Key Functions:**
- `process_invoice()`: Orchestrates the full processing pipeline
- `main()`: Main application entry point with tabbed interface

### 2. **Agentic System** (`agents/invoice_agent.py`)

**Technology:** LangGraph + LangChain + OpenAI

**Core Class:** `InvoiceProcessingAgent`

**State Management:**
```python
class InvoiceState(TypedDict):
    file_name: str           # Original filename
    ocr_text: str            # Raw OCR output
    clean_text: str          # AI-cleaned text
    extracted_data: dict     # Structured JSON data
    validation_status: str   # "valid" | "warning" | "invalid"
    errors: list            # Validation errors/warnings
    step: str               # Current processing step
```

**Agent Nodes:**

1. **Clean OCR Node** (`_clean_ocr_node`)
   - **Purpose:** Fix OCR errors and normalize text
   - **AI Model:** GPT (configurable)
   - **Input:** Raw OCR text
   - **Output:** Cleaned, normalized text
   - **Error Handling:** Falls back to original OCR text

2. **Extract Data Node** (`_extract_data_node`)
   - **Purpose:** Extract structured JSON from cleaned text
   - **AI Model:** GPT (configurable)
   - **Input:** Cleaned text
   - **Output:** Structured JSON with keys:
     - `vendor`, `number`, `date`, `total`, `currency`
     - `line_items` (array of items)
   - **Error Handling:** Returns empty dict on failure

3. **Validate Node** (`_validate_node`)
   - **Purpose:** Validate extracted data
   - **Logic:** Checks for required fields, data types, formats
   - **Output:** Validation status and error list
   - **No AI:** Pure rule-based validation

4. **Format Output Node** (`_format_output_node`)
   - **Purpose:** Prepare final output
   - **Output:** Completed state

**Graph Structure:**
```python
Entry → clean_ocr → extract_data → validate → format_output → END
```

### 3. **OCR Module** (`utils/ocr.py`)

**Technology:** EasyOCR

**Core Class:** `OCRReader`

**Features:**
- Lazy initialization (loads models only when needed)
- Supports multiple languages (default: English)
- GPU/CPU support
- Error handling

**Methods:**
- `read_text()`: Extract text from image (returns string)
- `read_text_detailed()`: Extract text with bounding boxes

### 4. **Database Layer** (`utils/database.py`)

**Technology:** SQLite

**Core Class:** `InvoiceDB`

**Schema:**
```sql
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL UNIQUE,
    vendor TEXT,
    number TEXT,
    date TEXT,
    total REAL,
    currency TEXT,
    raw_json TEXT,              -- Full processing result
    validation_status TEXT,     -- "valid" | "warning"
    errors TEXT,                -- JSON array of errors
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Methods:**
- `insert_invoice()`: Save processed invoice
- `get_all_invoices()`: Retrieve all invoices
- `get_invoice_by_id()`: Get specific invoice
- `delete_invoice()`: Remove invoice
- `get_stats()`: Get statistics (counts, totals, averages)

---

## 🔄 Data Flow

### Complete Processing Flow

```
1. USER UPLOADS IMAGE
   └─> Streamlit receives file (PNG/JPG/JPEG)

2. OCR EXTRACTION
   └─> OCRReader.read_text(image_path)
       └─> EasyOCR processes image
       └─> Returns raw text string
       └─> Example: "Vendor: Tech Solutions\nInvoice Number: INV-1001..."

3. AGENTIC PROCESSING (LangGraph)
   │
   ├─> Step 1: Clean OCR Node
   │   └─> GPT receives: Raw OCR text
   │   └─> GPT returns: Cleaned text
   │   └─> Example: "Vendor: Tech Solutions\nInvoice Number: INV-1001..."
   │
   ├─> Step 2: Extract Data Node
   │   └─> GPT receives: Cleaned text
   │   └─> GPT returns: JSON string
   │   └─> Parsed to: {
   │         "vendor": "Tech Solutions",
   │         "number": "INV-1001",
   │         "date": "2025-09-10",
   │         "total": 553.88,
   │         "currency": "EUR",
   │         "line_items": [...]
   │       }
   │
   ├─> Step 3: Validate Node
   │   └─> Checks: vendor, number, date, total, currency
   │   └─> Returns: validation_status, errors list
   │
   └─> Step 4: Format Output Node
       └─> Finalizes state
       └─> Returns complete result

4. DATABASE STORAGE
   └─> InvoiceDB.insert_invoice()
       └─> Saves to SQLite
       └─> Returns row ID

5. UI DISPLAY
   └─> Shows extracted data
   └─> Displays validation status
   └─> Updates statistics
```

### State Transformation

```
Initial State:
{
  file_name: "invoice_1.png",
  ocr_text: "Vendor: Tech...",
  clean_text: "",
  extracted_data: {},
  validation_status: "pending",
  errors: [],
  step: "started"
}

After Clean OCR:
{
  ...,
  clean_text: "Vendor: Tech Solutions\n...",
  step: "cleaned"
}

After Extract:
{
  ...,
  extracted_data: {"vendor": "Tech Solutions", ...},
  step: "extracted"
}

After Validate:
{
  ...,
  validation_status: "valid",
  errors: [],
  step: "validated"
}

Final State:
{
  ...,
  step: "completed"
}
```

---

## ⚙️ Environment Setup

### Prerequisites

1. **Python 3.8+**
   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **OpenAI API Key**
   - Sign up at https://platform.openai.com
   - Get API key from https://platform.openai.com/api-keys
   - You'll need credits in your OpenAI account

3. **System Requirements**
   - **RAM:** Minimum 4GB (8GB recommended)
   - **Storage:** ~2GB for Python packages and OCR models
   - **GPU:** Optional (for faster OCR, but CPU works fine)

### Step-by-Step Setup

#### 1. **Clone/Navigate to Project**
```bash
cd d:\downloads\invoice_generator
```

#### 2. **Create Virtual Environment** (Recommended)

**Windows:**
```bash
python -m venv invoice-env
invoice-env\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv invoice-env
source invoice-env/bin/activate
```

#### 3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

**This installs:**
- `streamlit` - Web UI framework
- `langgraph` - Agent orchestration
- `langchain` - LLM integration
- `langchain-openai` - OpenAI integration
- `easyocr` - OCR engine
- `pillow` - Image processing
- `pandas` - Data analysis
- `openai` - OpenAI SDK
- `numpy`, `torch` - ML dependencies (for EasyOCR)
- `python-dotenv` - Environment variable management

**Note:** First installation may take 5-10 minutes as it downloads:
- PyTorch (for EasyOCR)
- EasyOCR models (first run)

#### 4. **Set Up Environment Variables**

**Option A: Environment Variable (Temporary)**

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-proj-your-key-here"
```

**Windows (CMD):**
```cmd
set OPENAI_API_KEY=sk-proj-your-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="sk-proj-your-key-here"
```

**Option B: .env File (Persistent)**

Create a `.env` file in the project root:
```env
OPENAI_API_KEY=sk-proj-your-key-here
```

The app will automatically load this file.

#### 5. **Verify Setup**

```bash
python -c "import streamlit; import langgraph; import easyocr; print('✅ All imports successful!')"
```

---

## 🚀 How to Run

### Method 1: Using the Run Script (Recommended)

```bash
python run.py
```

This script:
- Checks for API key
- Starts Streamlit
- Opens browser automatically

### Method 2: Direct Streamlit Command

```bash
streamlit run app.py
```

### Method 3: With Environment Variable

**Windows:**
```powershell
$env:OPENAI_API_KEY="your-key"; streamlit run app.py
```

**Linux/Mac:**
```bash
OPENAI_API_KEY="your-key" streamlit run app.py
```

### Access the Application

Once running, the app will be available at:
- **Local:** http://localhost:8501
- Browser should open automatically

### First Run Notes

1. **EasyOCR Model Download:**
   - First OCR operation downloads models (~100MB)
   - This happens automatically
   - Subsequent runs are faster

2. **Database Creation:**
   - `invoice.db` is created automatically on first run
   - No manual setup needed

---

## 📁 Project Structure

```
invoice_generator/
│
├── app.py                      # Main Streamlit application
├── run.py                      # Quick start script
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── ARCHITECTURE.md            # This file
├── QUICKSTART.md              # Quick start guide
│
├── .streamlit/
│   └── config.toml            # Streamlit theme configuration
│
├── agents/
│   ├── __init__.py
│   └── invoice_agent.py      # LangGraph agent system
│
├── utils/
│   ├── __init__.py
│   ├── ocr.py                # EasyOCR wrapper
│   └── database.py           # SQLite operations
│
├── invoices/                  # Sample invoice images
│   ├── invoice_1.png
│   ├── invoice_2.png
│   └── ...
│
├── invoice.db                 # SQLite database (created automatically)
└── .env                       # Environment variables (create this)
```

---

## 🔍 Understanding the Code Flow

### When You Upload an Invoice:

1. **File Upload** (`app.py:154-162`)
   - User selects image file
   - Streamlit saves to temporary file

2. **OCR Processing** (`app.py:78-79`)
   ```python
   ocr_text = st.session_state.ocr_reader.read_text(temp_path)
   ```
   - EasyOCR extracts text from image
   - Returns raw text string

3. **Agentic Processing** (`app.py:82-86`)
   ```python
   result = st.session_state.agent.process(
       file_name=uploaded_file.name,
       ocr_text=ocr_text
   )
   ```
   - LangGraph executes agent workflow
   - Each node processes state sequentially
   - Returns complete result with all steps

4. **Database Storage** (`app.py:89-97`)
   ```python
   row_id = st.session_state.db.insert_invoice(...)
   ```
   - Saves to SQLite
   - Stores extracted data + full processing result

5. **UI Display** (`app.py:170-214`)
   - Shows extracted data in metrics
   - Displays processing steps
   - Shows validation status
   - Provides expandable sections for details

### Agent Processing Details:

**Entry Point:** `InvoiceProcessingAgent.process()`

```python
# 1. Create initial state
initial_state = {
    "file_name": "invoice.png",
    "ocr_text": "...",
    "clean_text": "",
    "extracted_data": {},
    "validation_status": "pending",
    "errors": [],
    "step": "started"
}

# 2. Invoke graph
result = self.graph.invoke(initial_state)

# 3. Graph executes nodes sequentially:
#    clean_ocr → extract_data → validate → format_output
```

**Each Node:**
- Receives current state
- Processes it (AI call or validation)
- Returns updated state
- State flows to next node

---

## 🎛️ Configuration Options

### Model Selection

In the Streamlit sidebar, you can choose:
- `gpt-4o-mini` (default) - Fast, cost-effective
- `gpt-4o` - More accurate, slower
- `gpt-3.5-turbo` - Fastest, less accurate

### Database Path

Default: `invoice.db` in project root

Change in `utils/database.py`:
```python
db = InvoiceDB(db_path="custom_path.db")
```

### OCR Settings

In `utils/ocr.py`, you can modify:
- Languages: `["en", "es", "fr"]` (default: `["en"]`)
- GPU: `gpu=True` (requires CUDA, default: `False`)

---

## 🐛 Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not found"**
   - Set environment variable or create `.env` file
   - Restart Streamlit after setting

2. **OCR is slow**
   - First run downloads models (one-time)
   - Use GPU for faster processing (if available)

3. **Import errors**
   - Ensure virtual environment is activated
   - Run: `pip install -r requirements.txt`

4. **Database errors**
   - Delete `invoice.db` to reset
   - Check file permissions

5. **Text not visible**
   - Check `.streamlit/config.toml` exists
   - Hard refresh browser (Ctrl+F5)

---

## 📊 Performance Considerations

### Processing Time (per invoice):
- **OCR:** 2-5 seconds (CPU) / 0.5-1 second (GPU)
- **AI Cleaning:** 2-4 seconds
- **AI Extraction:** 3-5 seconds
- **Validation:** <0.1 seconds
- **Total:** ~7-14 seconds per invoice

### Cost (OpenAI API):
- **gpt-4o-mini:** ~$0.001-0.002 per invoice
- **gpt-4o:** ~$0.01-0.02 per invoice
- **gpt-3.5-turbo:** ~$0.0005-0.001 per invoice

---

## 🔐 Security Notes

1. **API Key:**
   - Never commit `.env` file to git
   - Use environment variables in production
   - Rotate keys regularly

2. **Database:**
   - SQLite is file-based (not network-accessible)
   - Consider encryption for sensitive data
   - Regular backups recommended

3. **File Uploads:**
   - Temporary files are cleaned up automatically
   - No persistent storage of uploaded images

---

## 🚀 Next Steps

1. **Process Your First Invoice:**
   - Upload an invoice image
   - Watch the agentic pipeline work
   - View extracted data

2. **Explore Features:**
   - Browse processed invoices
   - Check analytics dashboard
   - View processing details

3. **Customize:**
   - Modify agent prompts in `invoice_agent.py`
   - Add custom validation rules
   - Extend database schema
