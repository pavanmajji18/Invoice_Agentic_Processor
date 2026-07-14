"""
LangGraph-based Agentic Invoice Processing System using OpenAI API
"""
import os
import json
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class InvoiceState(TypedDict):
    """State for the invoice processing agent"""
    file_name: str
    ocr_text: str
    clean_text: str
    extracted_data: dict
    validation_status: str
    errors: list
    step: str


class InvoiceProcessingAgent:
    """Agentic invoice processing system using standard LangGraph and OpenAI"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", api_key: str = None, temperature: float = 0.1):
        """Initialize the OpenAI ChatOpenAI and LangGraph"""
        key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model_name, temperature=temperature, openai_api_key=key)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(InvoiceState)
        
        # Add nodes
        workflow.add_node("clean_ocr", self._clean_ocr_node)
        workflow.add_node("extract_data", self._extract_data_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Define edges
        workflow.set_entry_point("clean_ocr")
        workflow.add_edge("clean_ocr", "extract_data")
        workflow.add_edge("extract_data", "validate")
        workflow.add_edge("validate", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow.compile()
    
    def _clean_ocr_node(self, state: InvoiceState) -> InvoiceState:
        """Clean and normalize OCR text using OpenAI"""
        try:
            messages = [
                SystemMessage(content="""You are an expert at cleaning noisy OCR text from invoices.
Your task is to:
- Fix character recognition errors
- Preserve all factual information
- Maintain table structure and readability
- Keep dates, numbers, and amounts accurate
- Remove artifacts and noise
Return ONLY the cleaned text, no explanations."""),
                HumanMessage(content=f"Clean this OCR text:\n\n{state['ocr_text']}")
            ]
            
            response = self.llm.invoke(messages)
            clean_text = response.content.strip()
            
            return {
                **state,
                "clean_text": clean_text,
                "step": "cleaned"
            }
        except Exception as e:
            return {
                **state,
                "clean_text": state.get("ocr_text", ""),
                "errors": state.get("errors", []) + [f"Clean error: {str(e)}"],
                "step": "clean_failed"
            }
    
    def _extract_data_node(self, state: InvoiceState) -> InvoiceState:
        """Extract structured JSON data from cleaned text using OpenAI"""
        try:
            messages = [
                SystemMessage(content="""You are an expert at extracting structured data from invoices.
Extract the following information and return ONLY valid JSON with these exact keys:
{
  "vendor": "company name or null",
  "number": "invoice number or null",
  "date": "YYYY-MM-DD format or null",
  "total": numeric value or null,
  "currency": "3-letter code (USD, EUR, etc.) or null",
  "line_items": [
    {
      "description": "item description",
      "quantity": numeric or null,
      "unit_price": numeric or null,
      "amount": numeric or null
    }
  ]
}
If information is not found, use null. Return ONLY the JSON, no markdown, no explanations."""),
                HumanMessage(content=f"Extract invoice data from:\n\n{state['clean_text']}")
            ]
            
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
            
            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    data = json.loads(content[start:end])
                else:
                    raise ValueError("No valid JSON found")
            
            return {
                **state,
                "extracted_data": data,
                "step": "extracted"
            }
        except Exception as e:
            return {
                **state,
                "extracted_data": {},
                "errors": state.get("errors", []) + [f"Extract error: {str(e)}"],
                "step": "extract_failed"
            }
    
    def _validate_node(self, state: InvoiceState) -> InvoiceState:
        """Validate extracted data"""
        data = state.get("extracted_data", {})
        errors = state.get("errors", [])
        warnings = []
        
        # Check required fields
        if not data.get("vendor"):
            warnings.append("Missing vendor name")
        if not data.get("number"):
            warnings.append("Missing invoice number")
        if not data.get("date"):
            warnings.append("Missing invoice date")
        if data.get("total") is None:
            warnings.append("Missing total amount")
        elif not isinstance(data.get("total"), (int, float)):
            warnings.append("Total is not numeric")
        
        # Validate currency
        currency = data.get("currency")
        if currency and len(currency) != 3:
            warnings.append(f"Invalid currency format: {currency}")
        
        # Validate date format
        date = data.get("date")
        if date and not isinstance(date, str):
            warnings.append("Date is not a string")
        
        status = "valid" if len(warnings) == 0 else "warning"
        
        return {
            **state,
            "validation_status": status,
            "errors": errors + warnings,
            "step": "validated"
        }
    
    def _format_output_node(self, state: InvoiceState) -> InvoiceState:
        """Format final output"""
        return {
            **state,
            "step": "completed"
        }
    
    def process(self, file_name: str, ocr_text: str) -> dict:
        """Process an invoice through the agentic pipeline"""
        initial_state: InvoiceState = {
            "file_name": file_name,
            "ocr_text": ocr_text,
            "clean_text": "",
            "extracted_data": {},
            "validation_status": "pending",
            "errors": [],
            "step": "started"
        }
        
        result = self.graph.invoke(initial_state)
        return result
