#!/usr/bin/env python3
"""Script to ingest MySQL database into the knowledge base."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mysql_ingestor import ingest_mysql


def main():
    """Ingest MySQL data into vector store."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest MySQL database into knowledge base")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the vector store before ingesting (removes all existing data)"
    )
    parser.add_argument(
        "--tables",
        type=str,
        help="Comma-separated list of specific tables to ingest (default: all tables)"
    )
    
    args = parser.parse_args()
    
    table_list = None
    if args.tables:
        table_list = [t.strip() for t in args.tables.split(",")]
        print(f"📋 Will ingest specific tables: {', '.join(table_list)}")
    else:
        print("📋 Will ingest all tables from the database")
    
    if args.reset:
        print("⚠️  WARNING: This will reset the vector store and remove all existing data!")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            return 1
    
    print("\n" + "=" * 80)
    print("MySQL Database Ingestion")
    print("=" * 80 + "\n")
    
    try:
        count = ingest_mysql(reset=args.reset, table_names=table_list)
        print(f"\n✅ Successfully ingested {count} documents from MySQL database!")
        return 0
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

