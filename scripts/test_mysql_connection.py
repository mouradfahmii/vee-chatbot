#!/usr/bin/env python3
"""Test MySQL database connection and list all tables."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()


def main():
    """Test MySQL connection and list all tables."""
    # Database connection parameters
    # Load from environment variables if available, otherwise use defaults
    db_config = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_DATABASE', 'veeapp_db'),
        'user': os.getenv('DB_USERNAME', 'veeapp_mhaggag'),
        'password': os.getenv('DB_PASSWORD', '1P&2tQtpBE((Ckf)')
    }

    print("=" * 80)
    print("MySQL Database Connection Test")
    print("=" * 80)
    print("\nDatabase Configuration:")
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  Database: {db_config['database']}")
    print(f"  User: {db_config['user']}")
    print(f"  Password: {'*' * len(db_config['password'])} (hidden)")
    print()

    connection = None
    try:
        # Test connection
        print("Connecting to MySQL database...")
        connection = mysql.connector.connect(**db_config)
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ Successfully connected to MySQL Server version {db_info}")
            print(f"✅ Connected to database: {db_config['database']}")
            
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            database_name = cursor.fetchone()
            print(f"✅ Current database: {database_name[0]}")
            print()
            
            # List all tables
            print("=" * 80)
            print("LISTING ALL TABLES")
            print("=" * 80)
            print()
            
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            
            print(f"📊 Found {len(tables)} table(s) in the database:\n")
            
            # Display tables
            table_names = [table[0] for table in tables]
            for i, table_name in enumerate(table_names, 1):
                print(f"{i}. {table_name}")
            
            print()
            print("=" * 80)
            print("TABLE DETAILS")
            print("=" * 80)
            print()
            
            # Get detailed information about each table
            for table_name in table_names:
                print(f"📋 Table: {table_name}")
                print("-" * 80)
                
                # Get table structure
                cursor.execute(f"DESCRIBE {table_name};")
                columns = cursor.fetchall()
                
                print(f"Columns ({len(columns)}):")
                for col in columns:
                    null_info = 'NULL' if col[2] == 'YES' else 'NOT NULL'
                    default_info = f" DEFAULT {col[4]}" if col[4] else ""
                    print(f"  - {col[0]:<30} {col[1]:<20} {null_info}{default_info}")
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cursor.fetchone()[0]
                print(f"Row count: {row_count}")
                
                # Preview sample data (first 3 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                rows = cursor.fetchall()
                
                if rows:
                    # Get column names
                    cursor.execute(f"DESCRIBE {table_name};")
                    column_info = cursor.fetchall()
                    column_names = [col[0] for col in column_info]
                    
                    print(f"Sample data (first 3 rows):")
                    df = pd.DataFrame(rows, columns=column_names)
                    print(df.to_string(index=False))
                else:
                    print("  (No data in this table)")
                
                print()
            
    except Error as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        # Close connection
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("=" * 80)
            print("✅ MySQL connection closed")
            print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

