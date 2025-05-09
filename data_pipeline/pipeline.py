import asyncio
import logging
import json
import os
from datetime import datetime, timedelta

from data_pipeline.downloader import FederalRegistryDownloader
from data_pipeline.processor import FederalRegistryProcessor
from database.db_manager import DatabaseManager
from config import PROCESSED_DATA_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline')

class FederalRegistryPipeline:
    """Main pipeline to download, process, and store Federal Registry data."""
    
    def __init__(self):
        self.downloader = FederalRegistryDownloader()
        self.processor = FederalRegistryProcessor()
        self.db_manager = DatabaseManager()
        
    async def run_pipeline(self, days_to_fetch=7):
        """
        Run the complete pipeline: download -> process -> store in database.
        
        Args:
            days_to_fetch: Number of days in the past to fetch data for
            
        Returns:
            Number of documents stored in the database
        """
        try:
            # Step 1: Download data
            logger.info(f"Starting data download for the past {days_to_fetch} days")
            downloaded_files = await self.downloader.download_data(days_to_fetch)
            logger.info(f"Downloaded {len(downloaded_files)} files")
            
            # Get all raw data files
            all_raw_files = []
            for file_name in os.listdir(self.downloader.raw_data_dir):
                if file_name.startswith('federal_registry_') and file_name.endswith('.json'):
                    all_raw_files.append(os.path.join(self.downloader.raw_data_dir, file_name))
            
            logger.info(f"Found {len(all_raw_files)} total raw data files")
            
            # Step 2: Process data
            logger.info("Starting data processing")
            processed_files = await self.processor.process_data(all_raw_files)
            logger.info(f"Processed {len(processed_files)} files")
            
            if not processed_files:
                logger.warning("No files were processed. Check the downloaded data.")
                return 0
            
            # Step 3: Store in database
            logger.info("Starting database storage")
            documents_stored = 0
            
            # Ensure database connection is established
            await self.db_manager.connect()
            
            for file_path in processed_files:
                try:
                    with open(file_path, 'r') as f:
                        documents = json.load(f)
                    
                    if not documents:
                        logger.warning(f"No documents found in {file_path}")
                        continue
                    
                    # Store documents in database
                    stored_count = await self.db_manager.store_documents(documents)
                    documents_stored += stored_count
                    logger.info(f"Stored {stored_count} documents from {file_path}")
                    
                    # Log document types and agencies for verification
                    if stored_count > 0:
                        doc_types = set(doc.get('document_type') for doc in documents if doc.get('document_type'))
                        agency_names = set()
                        for doc in documents:
                            agency_names.update(doc.get('agency_names', []))
                        
                        logger.info(f"Document types in this batch: {doc_types}")
                        logger.info(f"Agencies in this batch: {agency_names}")
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    continue
            
            # Verify data was stored correctly
            if documents_stored > 0:
                # Check document types
                doc_types = await self.db_manager.get_document_types()
                logger.info(f"Total document types in database: {len(doc_types)}")
                
                # Check agencies
                agencies = await self.db_manager.get_agencies()
                logger.info(f"Total agencies in database: {len(agencies)}")
                
                # Check recent documents
                recent_docs = await self.db_manager.get_recent_documents(limit=5)
                logger.info(f"Most recent documents: {[doc.get('title') for doc in recent_docs]}")
            
            # Close database connection
            await self.db_manager.close()
            
            logger.info(f"Pipeline completed successfully. Stored {documents_stored} documents.")
            return documents_stored
            
        except Exception as e:
            logger.error(f"Error running pipeline: {str(e)}")
            # Ensure database connection is closed in case of error
            try:
                await self.db_manager.close()
            except:
                pass
            return 0

async def main():
    pipeline = FederalRegistryPipeline()
    # Fetch last 90 days of data for initial setup
    await pipeline.run_pipeline(days_to_fetch=90)

if __name__ == "__main__":
    asyncio.run(main())