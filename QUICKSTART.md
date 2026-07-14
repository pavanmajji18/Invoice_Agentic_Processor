# 🚀 Quick Start Guide

Get up and running with the Agentic Invoice Processor in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Your OpenAI API Key

**Option A: Environment Variable (Recommended)**
```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# Windows (CMD)
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
```

**Option B: .env File**
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

## Step 3: Run the App

**Easy way:**
```bash
python run.py
```

**Or directly:**
```bash
streamlit run app.py
```

## Step 4: Process Your First Invoice

1. The app opens in your browser at `http://localhost:8501`
2. Go to the **"Upload & Process"** tab
3. Click **"Choose an invoice image"** and select a PNG/JPG file
4. Click **"🚀 Process Invoice"**
5. Watch the magic happen! ✨

## 🎯 What Happens?

The agentic system:
1. **Extracts text** from the image using OCR
2. **Cleans the text** using AI to fix errors
3. **Extracts structured data** (vendor, invoice #, date, total, etc.)
4. **Validates** the extracted data
5. **Saves** everything to the database

## 📊 View Results

- **View Invoices Tab**: See all processed invoices
- **Analytics Tab**: View statistics and charts

## 🐛 Troubleshooting

**"OPENAI_API_KEY not found"**
- Make sure you set the API key (see Step 2)
- Restart the app after setting the key

**OCR is slow**
- First run downloads models (one-time)
- Subsequent runs are faster

**Import errors**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check you're using Python 3.8+

## 🎉 You're Ready!

Start processing invoices and see the agentic system in action!
