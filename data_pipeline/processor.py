import json
import os
import asyncio
import aiofiles
import logging
from datetime import datetime
import re

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('processor')

class FederalRegistryProcessor:
    """Processes downloaded Federal Registry data."""
    
    def __init__(self):
        self.raw_data_dir = RAW_DATA_DIR
        self.processed_data_dir = PROCESSED_DATA_DIR
    
    async def process_file(self, file_path):
        """
        Process a single downloaded file.
        
        Args:
            file_path: Path to the raw data file
            
        Returns:
            Path to the processed file
        """
        try:
            # Read the raw data
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
            
            data = json.loads(content)
            
            # Extract relevant information from the results
            processed_docs = []
            
            for doc in data.get('results', []):
                processed_doc = {
                    'document_number': doc.get('document_number'),
                    'document_type': doc.get('type'),
                    'title': doc.get('title'),
                    'publication_date': doc.get('publication_date'),
                    'abstract': doc.get('abstract') or '',
                    'agency_names': [a.get('name') for a in doc.get('agencies', [])],
                    'html_url': doc.get('html_url'),
                    'pdf_url': doc.get('pdf_url'),
                    'full_text_xml_url': doc.get('full_text_xml_url'),
                    'presidential_document_type': doc.get('presidential_document_type', {}).get('name') if doc.get('presidential_document_type') else None,
                    'signing_date': doc.get('signing_date'),
                    'executive_order_number': doc.get('executive_order_number'),
                    'topics': [t.get('name') for t in doc.get('topics', [])],
                }
                processed_docs.append(processed_doc)
            
            # Create output file name
            file_name = os.path.basename(file_path)
            processed_file_path = os.path.join(self.processed_data_dir, f"processed_{file_name}")
            
            # Write processed data to file
            async with aiofiles.open(processed_file_path, 'w') as f:
                await f.write(json.dumps(processed_docs, indent=2))
            
            logger.info(f"Successfully processed {file_path}")
            return processed_file_path
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return None
    
    async def process_data(self, file_paths):
        """
        Process downloaded Federal Registry data.
        
        Args:
            file_paths: List of file paths containing downloaded data
        
        Returns:
            List of paths to processed files
        """
        processed_file_paths = []
        
        for file_path in file_paths:
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                
                # Extract documents from the response
                documents = data.get('results', [])
                processed_docs = []
                
                for doc in documents:
                    try:
                        # Extract basic metadata
                        processed_doc = {
                            'document_number': doc.get('document_number'),
                            'publication_date': doc.get('publication_date'),
                            'title': doc.get('title'),
                            'type': doc.get('type'),
                            'abstract': doc.get('abstract', ''),
                            'html_url': doc.get('html_url'),
                            'pdf_url': doc.get('pdf_url'),
                            'full_text_xml_url': doc.get('full_text_xml_url'),
                            'agencies': [agency.get('name') for agency in doc.get('agencies', [])],
                            'docket_ids': doc.get('docket_ids', []),
                            'regulation_id_numbers': doc.get('regulation_id_numbers', []),
                            'comments_close_date': doc.get('comments_close_date'),
                            'effective_date': doc.get('effective_date'),
                            'citation': doc.get('citation'),
                            'page_length': doc.get('page_length'),
                            'start_page': doc.get('start_page'),
                            'end_page': doc.get('end_page'),
                            'raw_text': doc.get('raw_text', ''),
                            'processed_at': datetime.now().isoformat()
                        }
                        
                        # Clean and normalize text fields
                        for field in ['title', 'abstract', 'raw_text']:
                            if field in processed_doc:
                                processed_doc[field] = self._clean_text(processed_doc[field])
                        
                        # Add document to processed list
                        processed_docs.append(processed_doc)
                        
                    except Exception as e:
                        logger.error(f"Error processing document {doc.get('document_number')}: {str(e)}")
                        continue
                
                # Save processed documents to file
                if processed_docs:
                    # Create output file name
                    file_name = os.path.basename(file_path)
                    processed_file_path = os.path.join(self.processed_data_dir, f"processed_{file_name}")
                    
                    # Write processed data to file
                    async with aiofiles.open(processed_file_path, 'w') as f:
                        await f.write(json.dumps(processed_docs, indent=2))
                    
                    processed_file_paths.append(processed_file_path)
                    logger.info(f"Successfully processed {file_path} -> {processed_file_path}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue
        
        return processed_file_paths
    
    def _clean_text(self, text):
        """
        Clean and normalize text content.
        
        Args:
            text: Text to clean
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?-]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()

# For testing purposes
async def main():
    processor = FederalRegistryProcessor()
    processed_files = await processor.process_data()
    logger.info(f"Processed {len(processed_files)} files")

if __name__ == "__main__":
    asyncio.run(main())