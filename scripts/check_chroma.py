import chromadb
print(f"Chroma version: {chromadb.__version__}")
try:
    from chromadb.config import Settings
    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="./data/test_db"))
    print("Initialized 0.3.x client")
except Exception as e:
    print(f"0.3.x init failed: {e}")
    try:
        client = chromadb.PersistentClient(path="./data/test_db")
        print("Initialized 0.4.x client")
    except Exception as e2:
        print(f"0.4.x init failed: {e2}")
