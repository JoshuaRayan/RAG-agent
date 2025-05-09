import argparse
import asyncio
import logging

from data_pipeline.pipeline import FederalRegistryPipeline
from api.main import start as start_api

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

async def run_pipeline(days_to_fetch: int):
    """Run the data pipeline."""
    pipeline = FederalRegistryPipeline()
    await pipeline.run_pipeline(days_to_fetch=days_to_fetch)

def main():
    parser = argparse.ArgumentParser(description='Federal Registry Search System')
    parser.add_argument('--mode', choices=['pipeline', 'api'], required=True,
                      help='Mode to run: pipeline for data collection or api for the search server')
    parser.add_argument('--days', type=int, default=7,
                      help='Number of days to fetch data for (only used in pipeline mode)')
    
    args = parser.parse_args()
    
    if args.mode == 'pipeline':
        logger.info(f"Running pipeline for the past {args.days} days")
        asyncio.run(run_pipeline(args.days))
    else:
        logger.info("Starting API server")
        start_api()

if __name__ == "__main__":
    main()
