#!/usr/bin/env python3
"""
Service for querying coffee bean data from SQLite database with pagination support.
"""

import sqlite3
import os
from typing import List, Optional, Dict, Any, Tuple
from coffee_dto import CoffeeBeanDTO
from datetime import datetime, timedelta


class CoffeeQueryService:
    """Service for querying coffee bean data."""

    def __init__(self, db_path: str = "coffee_beans.db"):
        """
        Initialize the coffee query service.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        # Cache for latest data, expires per hour
        self._latest_data_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiration: Dict[str, datetime] = {}

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        return sqlite3.connect(self.db_path)

    def _dict_factory(self, cursor, row) -> Dict[str, Any]:
        """Convert row to dictionary."""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _is_cache_valid(self, provider: str) -> bool:
        """Check if cache is valid for a provider (less than 1 hour old)."""
        if provider not in self._cache_expiration:
            return False
        return datetime.now() < self._cache_expiration[provider]

    def get_latest_data_for_provider(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest data for a specific provider from latest_data table with caching.
        Cache expires every hour.
        
        Args:
            provider (str): Provider name
            
        Returns:
            dict: Latest data with year and month or None if not found
        """
        # Check if we have valid cached data
        if self._is_cache_valid(provider):
            return self._latest_data_cache.get(provider)
        
        # Query the latest_data table
        sql_query = "SELECT data_year, data_month FROM latest_data WHERE provider = ?"
        conn = self._get_db_connection()
        conn.row_factory = self._dict_factory
        
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query, (provider,))
            row = cursor.fetchone()
            
            if row:
                # Update cache with expiration time (1 hour from now)
                self._latest_data_cache[provider] = row
                self._cache_expiration[provider] = datetime.now() + timedelta(hours=1)
                return row
            else:
                # No data found, cache None result with expiration
                self._latest_data_cache[provider] = None
                self._cache_expiration[provider] = datetime.now() + timedelta(hours=1)
                return None
        finally:
            conn.close()

    def query_coffee_beans(self, sql_query: str, params: Optional[Tuple] = None, 
                          page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Query coffee bean data with pagination support.
        
        Args:
            sql_query (str): SQL query to execute (should SELECT from coffee_bean table)
            params (tuple): Query parameters
            page (int): Page number (1-based)
            page_size (int): Number of items per page (10, 50, or 100)
            
        Returns:
            dict: Paginated results with metadata
        """
        # Validate page size
        if page_size not in [10, 50, 100]:
            page_size = 10  # Default to 10 if invalid
            
        # Ensure page is at least 1
        if page < 1:
            page = 1
            
        offset = (page - 1) * page_size
        
        # Modify the query to add LIMIT and OFFSET
        # Remove any existing LIMIT clause and add our own
        base_query = sql_query.strip()
        if base_query.lower().startswith('select'):
            # Add LIMIT and OFFSET to the query
            paginated_query = f"{base_query} LIMIT {page_size} OFFSET {offset}"
        else:
            raise ValueError("SQL query must be a SELECT statement")
        
        conn = self._get_db_connection()
        conn.row_factory = self._dict_factory
        
        try:
            cursor = conn.cursor()
            
            # Execute the paginated query
            if params:
                cursor.execute(paginated_query, params)
            else:
                cursor.execute(paginated_query)
                
            rows = cursor.fetchall()
            
            # Convert rows to DTOs
            coffee_beans = [CoffeeBeanDTO.from_dict(row) for row in rows]
            
            # Get total count for pagination metadata
            # Create a COUNT query from the original query
            count_query = self._create_count_query(sql_query)
            if params:
                cursor.execute(count_query, params)
            else:
                cursor.execute(count_query)
                
            total_count = cursor.fetchone()['count']
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                'data': [bean.to_dict() for bean in coffee_beans],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_items': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        finally:
            conn.close()

    def _create_count_query(self, original_query: str) -> str:
        """Create a COUNT query from the original SELECT query."""
        # Simple approach: replace SELECT columns with SELECT COUNT(*)
        # This is a basic implementation and may need refinement for complex queries
        query_lower = original_query.lower()
        select_pos = query_lower.find('select')
        from_pos = query_lower.find('from')
        
        if select_pos != -1 and from_pos != -1 and from_pos > select_pos:
            count_query = "SELECT COUNT(*) as count " + original_query[from_pos:]
            # Remove any ORDER BY clause for count query
            order_by_pos = count_query.lower().find('order by')
            if order_by_pos != -1:
                count_query = count_query[:order_by_pos]
            return count_query
        else:
            raise ValueError("Invalid SQL query format")
            
    def get_coffee_bean_by_name(self, name: str, data_year: int, data_month: int) -> Optional[CoffeeBeanDTO]:
        """
        Get a specific coffee bean by name and date.
        
        Args:
            name (str): Coffee bean name
            data_year (int): Year of data
            data_month (int): Month of data
            
        Returns:
            CoffeeBeanDTO: Coffee bean data or None if not found
        """
        sql_query = "SELECT * FROM coffee_bean WHERE name = ? AND data_year = ? AND data_month = ?"
        conn = self._get_db_connection()
        conn.row_factory = self._dict_factory
        
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query, (name, data_year, data_month))
            row = cursor.fetchone()
            
            if row:
                return CoffeeBeanDTO.from_dict(row)
            return None
            
        finally:
            conn.close()
    
    def get_price_trends(self, name: str) -> List[Dict[str, Any]]:
        """
        Get price trends for a specific coffee bean across all time periods.
        
        Args:
            name (str): Coffee bean name
            
        Returns:
            List[Dict]: List of price data sorted by time in descending order
        """
        sql_query = """
        SELECT 
            name,
            data_year,
            data_month,
            price_per_kg
        FROM coffee_bean 
        WHERE name = ?
        ORDER BY data_year DESC, data_month DESC
        """
        
        conn = self._get_db_connection()
        conn.row_factory = self._dict_factory
        
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query, (name,))
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            return [
                {
                    'name': row['name'],
                    'data_year': row['data_year'],
                    'data_month': row['data_month'],
                    'price_per_kg': row['price_per_kg']
                }
                for row in rows
            ]
            
        finally:
            conn.close()

    def get_latest_coffee_beans(self, provider: Optional[str] = None, country: Optional[str] = None, 
                               bean_type: Optional[str] = None, page: int = 1, 
                               page_size: int = 10) -> Dict[str, Any]:
        """
        Get the latest coffee beans, optionally filtered by provider, country, and type.
        Uses cached latest data to get coffee beans from the specific year and month.
        
        Args:
            provider (str): Provider name to filter by (optional)
            country (str): Country name to filter by (optional)
            bean_type (str): Bean type to filter by (optional)
            page (int): Page number (1-based)
            page_size (int): Number of items per page (10, 50, or 100)
            
        Returns:
            dict: Paginated results with metadata
        """
        # Build base query and parameters
        conditions = []
        params = []
        
        # If provider is specified, use cached latest data for that provider
        if provider:
            latest_data = self.get_latest_data_for_provider(provider)
            if latest_data:
                # Query coffee beans for the specific year and month from latest data
                conditions.append("provider = ? AND data_year = ? AND data_month = ?")
                params.extend([provider, latest_data['data_year'], latest_data['data_month']])
            else:
                # Fallback to original query if no latest data found
                conditions.append("provider = ?")
                params.append(provider)
        
        # Add country filter if specified
        if country:
            conditions.append("country = ?")
            params.append(country)
            
        # Add type filter if specified
        if bean_type:
            conditions.append("type = ?")
            params.append(bean_type)
            
        # Build final query
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
            sql_query = f"SELECT * FROM coffee_bean {where_clause} ORDER BY name"
        else:
            # For no filters specified, get latest data for all providers
            sql_query = "SELECT * FROM coffee_bean ORDER BY data_year DESC, data_month DESC, name"
            
        return self.query_coffee_beans(sql_query, params=tuple(params), page=page, page_size=page_size)


# Example usage
if __name__ == "__main__":
    service = CoffeeQueryService()
    
    # Example 1: Get all coffee beans (first page, 10 items)
    result = service.get_latest_coffee_beans(page=1, page_size=10)
    print("All coffee beans (page 1):")
    print(f"Total items: {result['pagination']['total_items']}")
    print(f"Total pages: {result['pagination']['total_pages']}")
    print(f"Items on this page: {len(result['data'])}")
    
    # Example 2: Get latest coffee beans for a specific provider
    result = service.get_latest_coffee_beans(provider="Premium Coffee Co.", page=1, page_size=10)
    print("\nLatest coffee beans for Premium Coffee Co. (page 1):")
    print(f"Total items: {result['pagination']['total_items']}")
    print(f"Items on this page: {len(result['data'])}")