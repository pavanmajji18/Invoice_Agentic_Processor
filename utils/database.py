"""
Database utilities for invoice storage
"""
import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime


class InvoiceDB:
    """SQLite database for storing processed invoices"""
    
    def __init__(self, db_path: str = "invoice.db"):
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create database schema if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                vendor TEXT,
                number TEXT,
                date TEXT,
                total REAL,
                currency TEXT,
                raw_json TEXT,
                validation_status TEXT,
                errors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def insert_invoice(self, file_name: str, data: Dict[str, Any], 
                      raw_json: Dict[str, Any], validation_status: str = "valid",
                      errors: List[str] = None) -> int:
        """Insert a processed invoice into the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        errors_str = json.dumps(errors or [])
        raw_json_str = json.dumps(raw_json, ensure_ascii=False)
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO invoices 
                (file_name, vendor, number, date, total, currency, raw_json, 
                 validation_status, errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_name,
                data.get("vendor"),
                data.get("number"),
                data.get("date"),
                data.get("total"),
                data.get("currency"),
                raw_json_str,
                validation_status,
                errors_str
            ))
            
            row_id = cursor.lastrowid
            conn.commit()
            return row_id
        finally:
            conn.close()
    
    def get_all_invoices(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all invoices from the database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM invoices 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific invoice by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM invoices")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total) FROM invoices WHERE total IS NOT NULL")
        total_amount = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM invoices 
            WHERE validation_status = 'valid'
        """)
        valid_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_invoices": total,
            "valid_invoices": valid_count,
            "total_amount": total_amount,
            "average_amount": total_amount / total if total > 0 else 0
        }
