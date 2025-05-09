import aiomysql
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_manager')

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.pool = None
        
    async def connect(self):
        """Establish connection to the MySQL database."""
        try:
            self.pool = await aiomysql.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
                autocommit=True,
                charset='utf8mb4',
                cursorclass=aiomysql.DictCursor
            )
            logger.info("Successfully connected to the database")
            
            # Initialize database schema
            await self._initialize_db_schema()
            
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    async def close(self):
        """Close database connection."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection closed")
    
    async def _initialize_db_schema(self):
        """Initialize database schema if it doesn't exist."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Create documents table
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        document_number VARCHAR(100) UNIQUE,
                        document_type VARCHAR(100),
                        title VARCHAR(500),
                        publication_date DATE,
                        abstract TEXT,
                        html_url VARCHAR(500),
                        pdf_url VARCHAR(500),
                        full_text_xml_url VARCHAR(500),
                        presidential_document_type VARCHAR(100),
                        signing_date DATE,
                        executive_order_number VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                
                # Create agencies table
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agencies (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        agency_name VARCHAR(255),
                        UNIQUE(agency_name)
                    )
                """)
                
                # Create topics table
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS topics (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        topic_name VARCHAR(255),
                        UNIQUE(topic_name)
                    )
                """)
                
                # Create document_agencies table (many-to-many)
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_agencies (
                        document_id INT,
                        agency_id INT,
                        PRIMARY KEY (document_id, agency_id),
                        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                        FOREIGN KEY (agency_id) REFERENCES agencies(id) ON DELETE CASCADE
                    )
                """)
                
                # Create document_topics table (many-to-many)
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_topics (
                        document_id INT,
                        topic_id INT,
                        PRIMARY KEY (document_id, topic_id),
                        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
                    )
                """)
                
                logger.info("Database schema initialized")
    
    async def store_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Store documents in the database.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Number of documents stored
        """
        if not self.pool:
            await self.connect()
        
        documents_stored = 0
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for doc in documents:
                    try:
                        # Format dates
                        publication_date = doc.get('publication_date')
                        signing_date = doc.get('signing_date')
                        
                        # Skip if document is already in the database
                        await cursor.execute(
                            "SELECT id FROM documents WHERE document_number = %s",
                            (doc.get('document_number'),)
                        )
                        existing_doc = await cursor.fetchone()
                        
                        if existing_doc:
                            # Update existing document
                            await cursor.execute("""
                                UPDATE documents SET
                                    document_type = %s,
                                    title = %s,
                                    publication_date = %s,
                                    abstract = %s,
                                    html_url = %s,
                                    pdf_url = %s,
                                    full_text_xml_url = %s,
                                    presidential_document_type = %s,
                                    signing_date = %s,
                                    executive_order_number = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE document_number = %s
                            """, (
                                doc.get('type'),  # Changed from document_type to type to match processor output
                                doc.get('title'),
                                publication_date,
                                doc.get('abstract'),
                                doc.get('html_url'),
                                doc.get('pdf_url'),
                                doc.get('full_text_xml_url'),
                                doc.get('presidential_document_type'),
                                signing_date,
                                doc.get('executive_order_number'),
                                doc.get('document_number')
                            ))
                            
                            document_id = existing_doc[0]
                            
                            # Clear existing agency and topic associations
                            await cursor.execute("DELETE FROM document_agencies WHERE document_id = %s", (document_id,))
                            await cursor.execute("DELETE FROM document_topics WHERE document_id = %s", (document_id,))
                        else:
                            # Insert new document
                            await cursor.execute("""
                                INSERT INTO documents (
                                    document_number, document_type, title, publication_date,
                                    abstract, html_url, pdf_url, full_text_xml_url,
                                    presidential_document_type, signing_date, executive_order_number,
                                    created_at, updated_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """, (
                                doc.get('document_number'),
                                doc.get('type'),  # Changed from document_type to type to match processor output
                                doc.get('title'),
                                publication_date,
                                doc.get('abstract'),
                                doc.get('html_url'),
                                doc.get('pdf_url'),
                                doc.get('full_text_xml_url'),
                                doc.get('presidential_document_type'),
                                signing_date,
                                doc.get('executive_order_number')
                            ))
                            
                            document_id = cursor.lastrowid
                            documents_stored += 1
                        
                        # Process agencies
                        for agency_name in doc.get('agencies', []):  # Changed from agency_names to agencies to match processor output
                            if agency_name:
                                # Insert agency if it doesn't exist
                                await cursor.execute(
                                    "INSERT IGNORE INTO agencies (agency_name) VALUES (%s)",
                                    (agency_name,)
                                )
                                
                                # Get agency ID
                                await cursor.execute(
                                    "SELECT id FROM agencies WHERE agency_name = %s",
                                    (agency_name,)
                                )
                                agency_id = (await cursor.fetchone())[0]
                                
                                # Associate document with agency
                                await cursor.execute(
                                    "INSERT IGNORE INTO document_agencies (document_id, agency_id) VALUES (%s, %s)",
                                    (document_id, agency_id)
                                )
                        
                        # Process topics
                        for topic_name in doc.get('topics', []):
                            if topic_name:
                                # Insert topic if it doesn't exist
                                await cursor.execute(
                                    "INSERT IGNORE INTO topics (topic_name) VALUES (%s)",
                                    (topic_name,)
                                )
                                
                                # Get topic ID
                                await cursor.execute(
                                    "SELECT id FROM topics WHERE topic_name = %s",
                                    (topic_name,)
                                )
                                topic_id = (await cursor.fetchone())[0]
                                
                                # Associate document with topic
                                await cursor.execute(
                                    "INSERT IGNORE INTO document_topics (document_id, topic_id) VALUES (%s, %s)",
                                    (document_id, topic_id)
                                )
                        
                    except Exception as e:
                        logger.error(f"Error storing document {doc.get('document_number')}: {str(e)}")
                        # Log the full document for debugging
                        logger.debug(f"Problematic document: {json.dumps(doc, indent=2)}")
                        continue
        
        return documents_stored
    
    async def search_documents(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for documents based on query parameters.
        
        Args:
            query_params: Dictionary of search parameters
                - date_from: Start date for publication_date filter
                - date_to: End date for publication_date filter
                - document_type: Filter by document type
                - agency: Filter by agency name
                - topic: Filter by topic name
                - presidential_doc_type: Filter by presidential document type
                - keywords: Search in title and abstract
                - limit: Maximum number of results to return
                - offset: Offset for pagination
                
        Returns:
            List of matching documents
        """
        if not self.pool:
            await self.connect()
            
        # Build the SQL query
        sql = """
            SELECT DISTINCT d.*
            FROM documents d
            LEFT JOIN document_agencies da ON d.id = da.document_id
            LEFT JOIN agencies a ON da.agency_id = a.id
            LEFT JOIN document_topics dt ON d.id = dt.document_id
            LEFT JOIN topics t ON dt.topic_id = t.id
            WHERE 1=1
        """
        params = []
        
        # Apply filters
        if query_params.get('date_from'):
            sql += " AND d.publication_date >= %s"
            params.append(query_params['date_from'])
            
        if query_params.get('date_to'):
            sql += " AND d.publication_date <= %s"
            params.append(query_params['date_to'])
            
        if query_params.get('document_type'):
            sql += " AND d.document_type = %s"
            params.append(query_params['document_type'])
            
        if query_params.get('agency'):
            sql += " AND a.agency_name LIKE %s"
            params.append(f"%{query_params['agency']}%")
            
        if query_params.get('topic'):
            sql += " AND t.topic_name LIKE %s"
            params.append(f"%{query_params['topic']}%")
            
        if query_params.get('presidential_doc_type'):
            sql += " AND d.presidential_document_type LIKE %s"
            params.append(f"%{query_params['presidential_doc_type']}%")
            
        if query_params.get('keywords'):
            keywords = query_params['keywords']
            sql += " AND (d.title LIKE %s OR d.abstract LIKE %s)"
            params.extend([f"%{keywords}%", f"%{keywords}%"])
            
        if query_params.get('executive_order'):
            sql += " AND d.executive_order_number = %s"
            params.append(query_params['executive_order'])
        
        # Add order by
        sql += " ORDER BY d.publication_date DESC"
        
        # Add limit and offset
        limit = int(query_params.get('limit', 10))
        offset = int(query_params.get('offset', 0))
        sql += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Execute query
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, params)
                documents = await cursor.fetchall()
                
                # For each document, fetch related agencies and topics
                for doc in documents:
                    # Fetch agencies
                    await cursor.execute("""
                        SELECT a.agency_name
                        FROM agencies a
                        JOIN document_agencies da ON a.id = da.agency_id
                        WHERE da.document_id = %s
                    """, (doc['id'],))
                    agencies = await cursor.fetchall()
                    doc['agencies'] = [a['agency_name'] for a in agencies]
                    
                    # Fetch topics
                    await cursor.execute("""
                        SELECT t.topic_name
                        FROM topics t
                        JOIN document_topics dt ON t.id = dt.topic_id
                        WHERE dt.document_id = %s
                    """, (doc['id'],))
                    topics = await cursor.fetchall()
                    doc['topics'] = [t['topic_name'] for t in topics]
                    
                    # Convert dates to string format for JSON serialization
                    if doc.get('publication_date'):
                        doc['publication_date'] = doc['publication_date'].isoformat()
                    if doc.get('signing_date'):
                        doc['signing_date'] = doc['signing_date'].isoformat()
                    if doc.get('created_at'):
                        doc['created_at'] = doc['created_at'].isoformat()
                    if doc.get('updated_at'):
                        doc['updated_at'] = doc['updated_at'].isoformat()
                
                return documents
    
    async def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            Document dictionary or None if not found
        """
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
                document = await cursor.fetchone()
                
                if document:
                    # Fetch agencies
                    await cursor.execute("""
                        SELECT a.agency_name
                        FROM agencies a
                        JOIN document_agencies da ON a.id = da.agency_id
                        WHERE da.document_id = %s
                    """, (document_id,))
                    agencies = await cursor.fetchall()
                    document['agencies'] = [a['agency_name'] for a in agencies]
                    
                    # Fetch topics
                    await cursor.execute("""
                        SELECT t.topic_name
                        FROM topics t
                        JOIN document_topics dt ON t.id = dt.topic_id
                        WHERE dt.document_id = %s
                    """, (document_id,))
                    topics = await cursor.fetchall()
                    document['topics'] = [t['topic_name'] for t in topics]
                    
                    # Convert dates to string format for JSON serialization
                    if document.get('publication_date'):
                        document['publication_date'] = document['publication_date'].isoformat()
                    if document.get('signing_date'):
                        document['signing_date'] = document['signing_date'].isoformat()
                    if document.get('created_at'):
                        document['created_at'] = document['created_at'].isoformat()
                    if document.get('updated_at'):
                        document['updated_at'] = document['updated_at'].isoformat()
                
                return document
    
    async def get_recent_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent documents.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of document dictionaries
        """
        return await self.search_documents({
            'limit': limit,
            'offset': 0
        })
    
    async def get_document_types(self) -> List[str]:
        """
        Get all document types in the database.
        
        Returns:
            List of document type strings
        """
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT DISTINCT document_type FROM documents")
                types = await cursor.fetchall()
                return [t[0] for t in types if t[0]]
    
    async def get_agencies(self) -> List[str]:
        """
        Get all agencies in the database.
        
        Returns:
            List of agency name strings
        """
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT agency_name FROM agencies ORDER BY agency_name")
                agencies = await cursor.fetchall()
                return [a[0] for a in agencies if a[0]]
    
    async def get_topics(self) -> List[str]:
        """
        Get all topics in the database.
        
        Returns:
            List of topic name strings
        """
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT topic_name FROM topics ORDER BY topic_name")
                topics = await cursor.fetchall()
                return [t[0] for t in topics if t[0]]
    
    async def get_presidential_document_types(self) -> List[str]:
        """
        Get all presidential document types in the database.
        
        Returns:
            List of presidential document type strings
        """
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT DISTINCT presidential_document_type FROM documents WHERE presidential_document_type IS NOT NULL"
                )
                types = await cursor.fetchall()
                return [t[0] for t in types if t[0]]