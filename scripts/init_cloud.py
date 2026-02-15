import os
import time
from pinecone import Pinecone, ServerlessSpec

def init_cloud():
    api_key = os.getenv("JCAPY_PINECONE_API_KEY")
    if not api_key:
        print("❌ Error: JCAPY_PINECONE_API_KEY not set.")
        return

    pc = Pinecone(api_key=api_key)
    index_name = os.getenv("JCAPY_PINECONE_INDEX", "jcapy-team-memory")

    print(f"☁️  Checking Pinecone Index: {index_name}...")

    # Check if index exists
    existing_indexes = [i.name for i in pc.list_indexes()]

    if index_name in existing_indexes:
        print(f"✅ Index '{index_name}' already exists.")
    else:
        print(f"🚀 Creating Serverless Index '{index_name}'...")
        try:
            pc.create_index(
                name=index_name,
                dimension=1536, # OpenAI text-embedding-ada-002 standard
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"✅ Index creation initiated. Waiting for readiness...")
            while not pc.describe_index(index_name).status['ready']:
                time.sleep(1)
            print(f"✨ Index '{index_name}' is ready!")
        except Exception as e:
            print(f"❌ Failed to create index: {e}")

if __name__ == "__main__":
    init_cloud()
