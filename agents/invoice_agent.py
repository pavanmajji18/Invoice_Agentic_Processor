"""
LangGraph-based Agentic Invoice Processing System using Euri AI SDK
"""
import os
import json
import re
from typing import Dict, Any, List
from euriai.langgraph import EuriaiLangGraph


class InvoiceProcessingAgent:
    """Agentic invoice processing system using EuriaiLangGraph"""
    
    def __init__(self, model_name: str = "gpt-4.1-nano", api_key: str = None):
        """Initialize Euriai LangGraphs for cleaning and extraction"""
        self.api_key = api_key or os.getenv("EURI_API_KEY")
        self.model_name = model_name
        
        # Node 1: Clean Graph
        self.clean_graph = EuriaiLangGraph(api_key=self.api_key, default_model=self.model_name)
        self.clean_graph.add_ai_node(
            "CLEAN",
            """You clean noisy OCR to plain text.
- Keep facts.
- No guessing.
- Keep table rows readable.

OCR:
{ocr_text}"""
        )
        self.clean_graph.set_entry_point("CLEAN")
        self.clean_graph.set_finish_point("CLEAN")
        
        # Node 2: Extract Graph
        self.extract_graph = EuriaiLangGraph(api_key=self.api_key, default_model=self.model_name)
        self.extract_graph.add_ai_node(
            "EXTRACT",
            """From CLEAN_TEXT, return STRICT JSON with keys exactly:
vendor, number, date, total, currency,
line_items (list of {{description, quantity, unit_price, amount}}).

Unknown → null. Numbers numeric. Dates YYYY-MM-DD if possible.
JSON ONLY, no extra text.

CLEAN_TEXT:
{clean_text}"""
        )
        self.extract_graph.set_entry_point("EXTRACT")
        self.extract_graph.set_finish_point("EXTRACT")

    def _pick_text(self, x, prefer_key=None) -> str:
        """Return a plain string from various possible structures"""
        if isinstance(x, str):
            return x
        if isinstance(x, dict):
            if prefer_key and prefer_key in x and isinstance(x[prefer_key], str):
                return x[prefer_key]
            for k in ("output", "text", "CLEAN_output", "EXTRACT_output"):
                if k in x and isinstance(x[k], str):
                    return x[k]
            return json.dumps(x, ensure_ascii=False)
        return str(x)

    def _parse_json_safe(self, raw) -> dict:
        """Parse JSON robustly, falling back to substring search if needed"""
        if isinstance(raw, dict):
            return raw
        if not isinstance(raw, str):
            return {"__raw__": raw}
        try:
            return json.loads(raw)
        except Exception:
            pass
        try:
            s, e = raw.find("{"), raw.rfind("}")
            if s != -1 and e != -1 and e > s:
                return json.loads(raw[s:e+1])
        except Exception:
            pass
        return {"__raw__": raw}

    def _heuristic_extract(self, clean_text: str) -> dict:
        """Heuristic regex-based extraction as a fallback when AI extraction is down"""
        def find(pat, s):
            m = re.search(pat, s, re.IGNORECASE)
            return m.group(1).strip() if m else None

        vendor = find(r"Vendor:\s*(.+)", clean_text)
        number = find(r"(?:Invoice Number|Invoice No\.?):\s*([A-Za-z0-9\-]+)", clean_text)
        date   = find(r"(?:Invoice Date|Date):\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", clean_text)
        total  = find(r"Total:\s*([0-9]+(?:\.[0-9]+)?)", clean_text)
        curr   = find(r"Total:\s*[0-9]+(?:\.[0-9]+)?\s*([A-Za-z]{3})", clean_text) or find(r"Currency:\s*([A-Za-z]{3})", clean_text)

        try:
            total = float(total) if total is not None else None
        except:
            total = None

        return {
            "vendor": vendor,
            "number": number,
            "date": date,
            "total": total,
            "currency": curr,
            "line_items": []
        }

    def _validate(self, data: dict) -> tuple[str, list[str]]:
        """Validate extracted data structures and fields"""
        issues = []
        for k in ["vendor", "number", "date", "currency"]:
            if k not in data or data.get(k) in (None, ""):
                issues.append(f"Missing key: {k}")
        try:
            if data.get("total") is None:
                issues.append("Total is null")
            else:
                float(data.get("total"))
        except Exception:
            issues.append(f"Total not numeric: {data.get('total')}")
        
        if not isinstance(data.get("line_items", []), list):
            issues.append("line_items not a list")
        
        status = "valid" if len(issues) == 0 else "warning"
        return status, issues

    def process(self, file_name: str, ocr_text: str) -> dict:
        """Process invoice: OCR Text -> Clean -> Extract -> Validate"""
        # Node 1: Clean
        clean_text = ocr_text
        clean_raw = {}
        clean_error = None
        try:
            clean_raw = self.clean_graph.run({"ocr_text": ocr_text})
            # Check for error signature in Euri response
            if isinstance(clean_raw, dict) and ("CLEAN_error" in clean_raw or "CLEAN_output" not in clean_raw):
                raise RuntimeError(clean_raw.get("CLEAN_error", "No CLEAN_output key found"))
            
            clean_text = self._pick_text(clean_raw, prefer_key="CLEAN_output")
            if not isinstance(clean_text, str) or not clean_text.strip():
                raise RuntimeError("Empty CLEAN output")
        except Exception as e:
            clean_error = f"Clean fallback: {str(e)}"
            clean_raw = {"fallback": True, "error": str(e)}

        # Node 2: Extract
        extract_raw = {}
        extract_error = None
        try:
            extract_raw = self.extract_graph.run({"clean_text": clean_text})
            # Check for error signature in Euri response
            if isinstance(extract_raw, dict) and ("EXTRACT_error" in extract_raw or "EXTRACT_output" not in extract_raw):
                raise RuntimeError(extract_raw.get("EXTRACT_error", "No EXTRACT_output key found"))
            
            raw_json = self._pick_text(extract_raw, prefer_key="EXTRACT_output")
        except Exception as e:
            extract_error = f"Extract fallback: {str(e)}"
            heuristic_data = self._heuristic_extract(clean_text)
            raw_json = json.dumps(heuristic_data, ensure_ascii=False)
            extract_raw = {"fallback": True, "error": str(e)}

        # Parse JSON
        extracted_data = self._parse_json_safe(raw_json)

        # Node 3: Validate
        status, validation_issues = self._validate(extracted_data)

        # Gather errors
        errors = []
        if clean_error:
            errors.append(clean_error)
        if extract_error:
            errors.append(extract_error)
        errors.extend(validation_issues)

        return {
            "file_name": file_name,
            "ocr_text": ocr_text,
            "clean_text": clean_text,
            "extracted_data": extracted_data,
            "validation_status": status,
            "errors": errors,
            "clean_raw": clean_raw,
            "extract_raw": extract_raw
        }
