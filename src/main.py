from pathlib import Path
from converter import FlatFileConverter
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Initialize paths
    input_dir = Path('input')
    output_dir = Path('output')
    specs_dir = Path('specs')
    
    # Create directories if they don't exist
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    specs_dir.mkdir(exist_ok=True)
    
    # Process ADF files
    spec_path = specs_dir / 'adf.yaml'
    
    try:
        converter = FlatFileConverter(spec_path)
        input_file = input_dir / "adf.txt"
        output_file = output_dir / "adf.csv"
        
        if not input_file.exists():
            logger.warning(f"Input file not found: {input_file}")
            return
            
        logger.info(f"Converting {input_file} using {spec_path}")
        converter.convert_file(input_file, output_file)
        logger.info(f"Successfully created {output_file}")
        
    except Exception as e:
        logger.error(f"Error processing ADF file: {str(e)}")

if __name__ == '__main__':
    main() 