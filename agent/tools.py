import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from database.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tools')

class FederalRegistryTools:
    """Tools for querying Federal Registry data."""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        
    async def connect(self):
        """Connect to the database."""
        await self.db_manager.connect()
    
    async def close(self):
        """Close the database connection."""
        await self.db_manager.close()
    
    async def search_documents(self, 
                            keywords: Optional[str] = None, 
                            date_from: Optional[str] = None, 
                            date_to: Optional[str] = None,
                            document_type: Optional[str] = None,
                            agency: Optional[str] = None,
                            topic: Optional[str] = None,
                            presidential_doc_type: Optional[str] = None,
                            executive_order: Optional[str] = None,
                            limit: int = 10,
                            offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search for documents based on various criteria.
        
        Args:
            keywords: Search terms to look for in title and abstract
            date_from: Start date for publication_date filter (YYYY-MM-DD)
            date_to: End date for publication_date filter (YYYY-MM-DD)
            document_type: Filter by document type
            agency: Filter by agency name
            topic: Filter by topic name
            presidential_doc_type: Filter by presidential document type
            executive_order: Filter by executive order number
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of matching documents
        """
        query_params = {
            'keywords': keywords,
            'date_from': date_from,
            'date_to': date_to,
            'document_type': document_type,
            'agency': agency,
            'topic': topic,
            'presidential_doc_type': presidential_doc_type,
            'executive_order': executive_order,
            'limit': limit,
            'offset': offset
        }
        
        # Clean up None values
        query_params = {k: v for k, v in query_params.items() if v is not None}
        
        try:
            documents = await self.db_manager.search_documents(query_params)
            return documents
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def get_recent_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent documents.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of document dictionaries
        """
        try:
            return await self.db_manager.get_recent_documents(limit)
        except Exception as e:
            logger.error(f"Error getting recent documents: {str(e)}")
            return []
    
    async def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            return await self.db_manager.get_document_by_id(document_id)
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None
    
    async def get_document_types(self) -> List[str]:
        """
        Get all document types in the database.
        
        Returns:
            List of document type strings
        """
        try:
            return await self.db_manager.get_document_types()
        except Exception as e:
            logger.error(f"Error getting document types: {str(e)}")
            return []
    
    async def get_agencies(self) -> List[str]:
        """
        Get all agencies in the database.
        
        Returns:
            List of agency name strings
        """
        try:
            return await self.db_manager.get_agencies()
        except Exception as e:
            logger.error(f"Error getting agencies: {str(e)}")
            return []
    
    async def get_topics(self) -> List[str]:
        """
        Get all topics in the database.
        
        Returns:
            List of topic name strings
        """
        try:
            return await self.db_manager.get_topics()
        except Exception as e:
            logger.error(f"Error getting topics: {str(e)}")
            return []
    
    async def get_presidential_document_types(self) -> List[str]:
        """
        Get all presidential document types in the database.
        
        Returns:
            List of presidential document type strings
        """
        try:
            return await self.db_manager.get_presidential_document_types()
        except Exception as e:
            logger.error(f"Error getting presidential document types: {str(e)}")
            return []
    
    async def search_recent_executive_orders(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for recent executive orders.
        
        Args:
            days: Number of days in the past to search
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        return await self.search_documents(
            presidential_doc_type="Executive Order",
            date_from=date_from,
            limit=limit
        )
    
    async def search_documents_by_date_range(self, start_date: str, end_date: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        return await self.search_documents(
            date_from=start_date,
            date_to=end_date,
            limit=limit
        )
    
    async def search_by_agency_and_topic(self, agency: str, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents by agency and topic.
        
        Args:
            agency: Agency name
            topic: Topic name
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        return await self.search_documents(
            agency=agency,
            topic=topic,
            limit=limit
        )