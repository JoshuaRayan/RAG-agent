import asyncio
from database.db_manager import DatabaseManager

async def test_database():
    db = DatabaseManager()
    try:
        await db.connect()
        
        # Test getting recent documents
        print("\nTesting recent documents:")
        docs = await db.get_recent_documents(limit=5)
        print(f"Found {len(docs)} recent documents")
        for doc in docs:
            print(f"- {doc.get('title', 'No title')} ({doc.get('publication_date', 'No date')})")
        
        # Test getting document types
        print("\nTesting document types:")
        types = await db.get_document_types()
        print(f"Found {len(types)} document types:")
        print(types)
        
        # Test getting agencies
        print("\nTesting agencies:")
        agencies = await db.get_agencies()
        print(f"Found {len(agencies)} agencies:")
        print(agencies)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_database())