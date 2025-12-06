from __future__ import annotations

import os
from typing import Dict, List, Optional

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

from app.vector_store import Document, vector_store

load_dotenv()


class MySQLIngestor:
    """Reads data from MySQL database and converts it to vector store documents."""

    def __init__(self) -> None:
        """Initialize MySQL connection parameters from environment."""
        self.db_config = {
            'host': os.getenv('DB_HOST', '127.0.0.1'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'database': os.getenv('DB_DATABASE', 'veeapp_db'),
            'user': os.getenv('DB_USERNAME', 'veeapp_mhaggag'),
            'password': os.getenv('DB_PASSWORD', '1P&2tQtpBE((Ckf)')
        }
        self.connection: Optional[mysql.connector.MySQLConnection] = None

    def connect(self) -> None:
        """Establish connection to MySQL database."""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if not self.connection.is_connected():
                raise RuntimeError("Failed to connect to MySQL database")
        except Error as e:
            raise RuntimeError(f"Error connecting to MySQL: {e}") from e

    def disconnect(self) -> None:
        """Close MySQL connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("Not connected to database")
        
        cursor = self.connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        return tables

    def get_table_structure(self, table_name: str) -> List[Dict]:
        """Get column information for a table."""
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("Not connected to database")
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(f"DESCRIBE {table_name};")
        columns = cursor.fetchall()
        cursor.close()
        return columns

    def get_table_data(self, table_name: str, limit: Optional[int] = None) -> List[Dict]:
        """Get all data from a table."""
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("Not connected to database")
        
        cursor = self.connection.cursor(dictionary=True)
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def table_to_documents(
        self, 
        table_name: str, 
        table_rows: List[Dict],
        table_columns: List[Dict]
    ) -> List[Document]:
        """
        Convert table rows to Document objects.
        
        Creates a document for each row with:
        - Content: Human-readable description of the row
        - Metadata: All column values for filtering
        - Doc ID: table_name::primary_key or table_name::row_index
        """
        documents: List[Document] = []
        column_names = [col['Field'] for col in table_columns]
        
        # Try to find primary key or ID column
        primary_key = None
        for col in table_columns:
            if col.get('Key') == 'PRI':
                primary_key = col['Field']
                break
        if not primary_key:
            # Look for common ID column names
            for col_name in ['id', 'ID', 'Id', table_name.lower() + '_id']:
                if col_name in column_names:
                    primary_key = col_name
                    break

        for idx, row in enumerate(table_rows):
            # Build human-readable content
            content_parts = []
            for col_name, value in row.items():
                if value is not None:
                    # Format based on column type
                    if isinstance(value, (int, float)):
                        content_parts.append(f"{col_name}: {value}")
                    elif isinstance(value, str):
                        # Truncate long strings
                        value_str = value[:200] + "..." if len(value) > 200 else value
                        content_parts.append(f"{col_name}: {value_str}")
                    else:
                        content_parts.append(f"{col_name}: {str(value)}")
            
            content = f"From {table_name} table: " + ". ".join(content_parts)
            
            # Create doc_id
            if primary_key and primary_key in row:
                doc_id = f"mysql::{table_name}::{row[primary_key]}"
            else:
                doc_id = f"mysql::{table_name}::{idx}"
            
            # Create metadata with all row data plus table info
            metadata = {
                "type": "mysql_data",
                "source_table": table_name,
                **{k: str(v) if v is not None else "" for k, v in row.items()}
            }
            
            documents.append(Document(doc_id=doc_id, content=content, metadata=metadata))
        
        return documents

    def ingest_table(self, table_name: str) -> int:
        """Ingest a single table into the vector store."""
        print(f"📊 Processing table: {table_name}")
        
        # Get table structure
        columns = self.get_table_structure(table_name)
        
        # Get all data from table
        rows = self.get_table_data(table_name)
        
        if not rows:
            print(f"  ⚠️  Table {table_name} is empty, skipping")
            return 0
        
        # Convert to documents
        documents = self.table_to_documents(table_name, rows, columns)
        
        # Add to vector store
        vector_store.add(documents)
        
        print(f"  ✅ Added {len(documents)} documents from {table_name}")
        return len(documents)

    def ingest_all_tables(self, table_names: Optional[List[str]] = None) -> int:
        """
        Ingest all tables or specified tables into the vector store.
        
        Args:
            table_names: Optional list of table names to ingest. If None, ingests all tables.
        
        Returns:
            Total number of documents added
        """
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        try:
            if table_names is None:
                table_names = self.get_all_tables()
            
            print(f"\n🔄 Starting MySQL ingestion for {len(table_names)} table(s)...")
            print("=" * 80)
            
            total_docs = 0
            for table_name in table_names:
                try:
                    count = self.ingest_table(table_name)
                    total_docs += count
                except Exception as e:
                    print(f"  ❌ Error processing {table_name}: {e}")
                    continue
            
            print("=" * 80)
            print(f"✅ MySQL ingestion complete! Added {total_docs} total documents")
            return total_docs
            
        finally:
            self.disconnect()

    def run(self, reset: bool = False, table_names: Optional[List[str]] = None) -> int:
        """
        Run the ingestion process.
        
        Args:
            reset: If True, reset the vector store before adding new documents
            table_names: Optional list of specific tables to ingest. If None, ingests all.
        
        Returns:
            Number of documents added
        """
        if reset:
            print("🔄 Resetting vector store...")
            vector_store.reset()
        
        return self.ingest_all_tables(table_names)


def ingest_mysql(reset: bool = False, table_names: Optional[List[str]] = None) -> int:
    """
    Convenience function to ingest MySQL data.
    
    Args:
        reset: If True, reset the vector store before adding
        table_names: Optional list of specific tables to ingest
    
    Returns:
        Number of documents added
    """
    ingestor = MySQLIngestor()
    return ingestor.run(reset=reset, table_names=table_names)

