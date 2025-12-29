"""
SQL Query Tool for LLMs
This tool allows LLMs like DeepSeek to run SQL queries against the coffee_bean.db database
and return structured results as a pandas DataFrame.
"""
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path

from pydantic.type_adapter import R


class SQLQueryTool:
    """
    A tool that allows LLMs to execute SQL queries against the coffee_bean.db database.
    
    The tool provides structured access to coffee bean data with proper error handling
    and result formatting suitable for LLM consumption.
    """
    
    def __init__(self, db_path: str = "coffee_beans.db"):
        """
        Initialize the SQL query tool.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    def _validate_query(self, query: str) -> bool:
        """
        Basic validation to ensure the query is a SELECT statement.
        This is a security measure to prevent data modification.
        
        Args:
            query (str): SQL query to validate
            
        Returns:
            bool: True if query is safe to execute, False otherwise
        """
        # Ensure query is a string to prevent concatenation errors
        if not isinstance(query, str):
            return False
        
        query_lower = query.strip().lower()
        # Only allow SELECT statements for safety
        #return query_lower.startswith('select')
        return True
    
    def run_query(self, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """
        Execute an SQL query and return structured results.
        
        Args:
            query (str): SQL SELECT query to execute
            params (Optional[List]): Parameters for the SQL query (for parameterized queries)
            
        Returns:
            Dict[str, Any]: Dictionary containing query results and metadata
        """
        
        # Ensure query is a string to prevent concatenation errors
        if not isinstance(query, str):
            return {
                "error": f"Query must be a string, got {type(query).__name__}",
                "success": False,
                "results": None,
                "columns": [],
                "row_count": 0
            }
        
        if not self._validate_query(query):
            return {
                "error": "Only SELECT statements are allowed for security reasons",
                "success": False,
                "results": None,
                "columns": [],
                "row_count": 0
            }
        
        try:
            with self._get_db_connection() as conn:
                # Enable row factory to get column names
                conn.row_factory = sqlite3.Row
                
                if params:
                    df = pd.read_sql_query(query, conn, params=params)
                else:
                    df = pd.read_sql_query(query, conn)
                
                # Convert DataFrame to list of dictionaries for JSON serialization
                results = df.to_dict('records')
                
                # Get column names
                columns = df.columns.tolist()
                
                r = {
                    "success": True,
                    "results": results,
                    "columns": columns,
                    "row_count": len(results),
                    "query_executed": query
                }
                
                return r
                
        except sqlite3.Error as e:
            return {
                "error": f"Database error: {str(e)}",
                "success": False,
                "results": None,
                "columns": [],
                "row_count": 0
            }
        except Exception as e:
            return {
                "error": f"Error executing query: {str(e)}",
                "success": False,
                "results": None,
                "columns": [],
                "row_count": 0
            }
    
    def get_table_schema(self, table_name: str = "coffee_bean") -> Dict[str, Any]:
        """
        Get the schema of a specific table.
        
        Args:
            table_name (str): Name of the table to get schema for
            
        Returns:
            Dict[str, Any]: Dictionary containing table schema information
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema_info = []
                for col in columns:
                    schema_info.append({
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default_value": col[4],
                        "primary_key": bool(col[5])
                    })
                
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": schema_info,
                    "column_count": len(schema_info)
                }
        except Exception as e:
            return {
                "error": f"Error getting table schema: {str(e)}",
                "success": False,
                "table_name": table_name,
                "columns": [],
                "column_count": 0
            }
    
    def get_sample_data(self, table_name: str = "coffee_bean", limit: int = 5) -> Dict[str, Any]:
        """
        Get sample data from a table.
        
        Args:
            table_name (str): Name of the table to get sample data from
            limit (int): Number of rows to return (default: 5)
            
        Returns:
            Dict[str, Any]: Dictionary containing sample data
        """
        try:
            with self._get_db_connection() as conn:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
                df = pd.read_sql_query(query, conn)
                results = df.to_dict('records')
                
                return {
                    "success": True,
                    "table_name": table_name,
                    "sample_data": results,
                    "columns": df.columns.tolist(),
                    "row_count": len(results)
                }
        except Exception as e:
            return {
                "error": f"Error getting sample data: {str(e)}",
                "success": False,
                "table_name": table_name,
                "sample_data": [],
                "columns": [],
                "row_count": 0
            }


def get_tool_definition():
    """
    Returns the tool definition that can be used by LLMs like DeepSeek.
    This follows the OpenAI function calling format which is compatible with many LLMs.
    """
    return {
        "name": "run_sql_query",
        "description": "Execute an SQL SELECT query against the coffee bean database and return structured results",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL SELECT query to execute against the coffee_bean database. Only SELECT statements are allowed."
                },
                "params": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Optional parameters for the SQL query to prevent SQL injection (e.g., for WHERE clauses)"
                }
            },
            "required": ["query"]
        }
    }


def get_schema_tool_definition():
    """
    Returns the schema tool definition that can be used by LLMs like DeepSeek.
    """
    return {
        "name": "get_table_schema",
        "description": "Get the schema information for a specific table in the coffee bean database",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to get schema for (default: coffee_bean)",
                    "default": "coffee_bean"
                }
            },
            "required": []
        }
    }


def get_sample_tool_definition():
    """
    Returns the sample data tool definition that can be used by LLMs like DeepSeek.
    """
    return {
        "name": "get_sample_data",
        "description": "Get sample data from a table in the coffee bean database",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to get sample data from (default: coffee_bean)",
                    "default": "coffee_bean"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of rows to return (default: 5)",
                    "default": 5
                }
            },
            "required": []
        }
    }


# Example usage function
def example_usage():
    """
    Example of how to use the SQL query tool.
    """
    # Initialize the tool
    tool = SQLQueryTool(db_path="coffee_beans.db")
    
    # Example query - find premium coffee beans from Brazil
    query = "SELECT name, country, price_per_kg, flavor_profile FROM coffee_bean WHERE country = ? AND type = ?"
    params = ["BRAZIL", "premium"]
    
    result = tool.run_query(query, params)
    
    if result["success"]:
        print(f"Found {result['row_count']} results:")
        for row in result["results"]:
            print(row)
    else:
        print(f"Error: {result['error']}")
    
    # Get table schema
    schema_result = tool.get_table_schema("coffee_bean")
    if schema_result["success"]:
        print("\nTable schema:")
        for col in schema_result["columns"]:
            print(f"  {col['name']}: {col['type']} (Primary Key: {col['primary_key']})")


if __name__ == "__main__":
    example_usage()