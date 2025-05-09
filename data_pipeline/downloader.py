import aiohttp
import aiofiles
import json
import os
import asyncio
from datetime import datetime, timedelta
import logging

from config import FEDERAL_REGISTRY_API_URL, RAW_DATA_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('downloader')

class FederalRegistryDownloader:
    """Downloads data from the Federal Registry API."""
    
    def __init__(self):
        self.api_url = FEDERAL_REGISTRY_API_URL
        self.raw_data_dir = RAW_DATA_DIR
        
    async def download_data(self, days_to_fetch=7):
        """
        Download Federal Registry data for the specified number of days.
        
        Args:
            days_to_fetch: Number of days in the past to fetch data for
        
        Returns:
            List of file paths where the downloaded data is stored
        """
        today = datetime.now()
        downloaded_files = []
        
        async with aiohttp.ClientSession() as session:
            for day_offset in range(days_to_fetch):
                target_date = today - timedelta(days=day_offset)
                date_str = target_date.strftime('%Y-%m-%d')
                
                # Format file path
                file_path = os.path.join(self.raw_data_dir, f"federal_registry_{date_str}.json")
                
                # Skip if file already exists and is less than 24 hours old
                if os.path.exists(file_path) and (datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))).total_seconds() < 86400:
                    logger.info(f"Skipping download for {date_str} - recent file exists")
                    downloaded_files.append(file_path)
                    continue
                
                # Prepare query parameters
                params = {
                    'conditions[publication_date][is]': date_str,
                    'per_page': 100,  # Maximum allowed by the API
                    'page': 1,
                    'order': 'newest'
                }
                
                try:
                    logger.info(f"Downloading data for {date_str}")
                    response = await session.get(self.api_url, params=params)
                    response.raise_for_status()
                    
                    data = await response.json()
                    
                    # Save the data to file
                    async with aiofiles.open(file_path, 'w') as f:
                        await f.write(json.dumps(data, indent=2))
                    
                    downloaded_files.append(file_path)
                    logger.info(f"Successfully downloaded data for {date_str}")
                    
                    # Check if there are more pages
                    total_pages = data.get('total_pages', 1)
                    current_page = data.get('current_page', 1)
                    
                    # Fetch additional pages if needed
                    while current_page < total_pages:
                        current_page += 1
                        params['page'] = current_page
                        
                        logger.info(f"Downloading page {current_page} for {date_str}")
                        response = await session.get(self.api_url, params=params)
                        response.raise_for_status()
                        
                        page_data = await response.json()
                        
                        # Save the data to file with page number
                        page_file_path = os.path.join(
                            self.raw_data_dir, 
                            f"federal_registry_{date_str}_page{current_page}.json"
                        )
                        
                        async with aiofiles.open(page_file_path, 'w') as f:
                            await f.write(json.dumps(page_data, indent=2))
                        
                        downloaded_files.append(page_file_path)
                        logger.info(f"Successfully downloaded page {current_page} for {date_str}")
                        
                        # Add a small delay to avoid rate limiting
                        await asyncio.sleep(0.5)
                    
                    # Add a delay between days to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error downloading data for {date_str}: {str(e)}")
                    continue
        
        return downloaded_files

# For testing purposes
async def main():
    downloader = FederalRegistryDownloader()
    files = await downloader.download_data(days_to_fetch=7)
    logger.info(f"Downloaded {len(files)} files")

if __name__ == "__main__":
    asyncio.run(main())