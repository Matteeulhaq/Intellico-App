"""
Clear all papers and related data from MongoDB
Use this to start fresh with a clean database
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def clear_database():
    """Clear all collections in the Intellico database"""

    # Get MongoDB URI from environment
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI not found in environment variables")
        return

    try:
        # Connect to MongoDB
        print(f"🔗 Connecting to MongoDB...")
        client = MongoClient(mongo_uri)
        db = client['intellico']

        # List all collections
        collections = ['chunks', 'papers', 'summaries', 'flowcharts', 'qa_cache']

        # Show what we're about to clear
        print("\n📊 Current database status:")
        total_documents = 0
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            total_documents += count
            print(f"  • {collection_name}: {count} documents")

        print(f"\n📦 Total documents to delete: {total_documents}")

        if total_documents == 0:
            print("✅ Database is already empty!")
            return

        # Ask for confirmation
        response = input("\n⚠️  Are you sure you want to clear ALL data? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return

        # Clear each collection
        print("\n🗑️  Clearing collections...")
        for collection_name in collections:
            result = db[collection_name].delete_many({})
            print(f"  ✓ Deleted {result.deleted_count} documents from {collection_name}")

        print("\n✅ Database cleared successfully!")
        print("🚀 You can now start fresh with paper uploads")

        # Close connection
        client.close()

    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        print(f"Make sure your MongoDB connection is working:")
        print(f"  • Check MONGO_URI in .env file")
        print(f"  • Ensure MongoDB is running")
        print(f"  • Verify connection credentials")

if __name__ == "__main__":
    clear_database()
