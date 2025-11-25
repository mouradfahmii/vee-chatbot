#!/usr/bin/env python3
"""CLI helper to rebuild the Chroma vector store from the synthetic dataset."""

from app.ingest import ingest_dataset


def main() -> None:
    count = ingest_dataset(reset=True)
    print(f"Indexed {count} documents into Chroma.")


if __name__ == "__main__":
    main()
