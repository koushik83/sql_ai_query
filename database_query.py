import sqlite3
from openai import OpenAI
from typing import List, Dict, Tuple

class DatabaseQuery:
    def __init__(self, db_path: str, api_key: str):
        self.db_path = db_path  # Store the path instead of creating connection
        self.client = OpenAI(api_key=api_key)
        self.schema_info = self._get_schema_info()
    
    def _get_connection(self):
        """Create a new connection for each operation"""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection
    
    def _get_schema_info(self) -> str:
        """Get schema and sample data for all tables."""
        schema_info = []
        
        with self._get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                sample_data = cursor.fetchall()
                
                schema_info.append(f"\nTable: {table_name}")
                schema_info.append("Columns: " + ", ".join(col[1] for col in columns))
                schema_info.append("Sample data:")
                for row in sample_data:
                    schema_info.append(str(dict(row)))
                
        return "\n".join(schema_info)

    def execute_query(self, sql_query: str) -> Tuple[List[str], List[Dict]]:
        """Execute SQL query and return results."""
        with self._get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql_query)
            
            columns = [description[0] for description in cursor.description]
            results = [dict(row) for row in cursor.fetchall()]
            
            return columns, results

    # The rest of the methods remain the same (generate_sql_query, generate_insights)
    def generate_sql_query(self, natural_query: str) -> str:
        """Convert natural language query to SQL using OpenAI."""
        prompt = f"""Given the following database schema and sample data:
        {self.schema_info}
        Convert this natural language query to SQL: "{natural_query}"
        Return ONLY the SQL query, nothing else. The query should be executable on a SQLite database."""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert SQL developer. Generate only SQL queries without any explanation or additional text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        return response.choices[0].message.content.strip()

    def generate_insights(self, natural_query: str = "Generate key business insights from this data") -> str:
        """Generate insights using OpenAI based on database schema and data."""
        prompt = f"""Given the following database schema and sample data:
        {self.schema_info}
        Please analyze this and provide insights for the following request: "{natural_query}"
        Focus on specific, data-driven insights that can provide business value."""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data analyst expert. Provide clear, actionable insights based on the data. Use specific numbers and patterns where possible."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()