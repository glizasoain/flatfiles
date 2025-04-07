from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import yaml
from datetime import datetime
import re

class FlatFileConverter:
    def __init__(self, spec_path: Path):
        """
        Initialize the converter with field specifications.
        
        Args:
            spec_path: Path to the YAML specification file
        """
        self.spec = self._load_spec(spec_path)
        self._validate_spec()
        
    def _load_spec(self, spec_path: Path) -> Dict:
        """Load field specifications from YAML file."""
        with open(spec_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _validate_spec(self) -> None:
        """Validate the loaded specification."""
        required_fields = ['name', 'description', 'record_length', 'fields']
        for field in required_fields:
            if field not in self.spec:
                raise ValueError(f"Missing required field '{field}' in specification")
        
        # Validate total length matches record_length
        total_length = sum(field['length'] for field in self.spec['fields'])
        if total_length != self.spec['record_length']:
            raise ValueError(
                f"Sum of field lengths ({total_length}) does not match "
                f"record_length ({self.spec['record_length']})"
            )
    
    def _convert_field_value(self, value: str, field: Dict[str, Any]) -> Any:
        """Convert field value based on its type."""
        value = value.strip()
        if not value:
            return None
            
        field_type = field.get('type', 'string')
        try:
            if field_type == 'integer':
                return int(value)
            elif field_type == 'decimal':
                # For ADF format, amount fields are in cents
                if field['name'] in ['amount', 'amount_of_withholding_tax']:
                    return float(value) / 100
                return float(value)
            elif field_type == 'date':
                return datetime.strptime(value, '%Y%m%d').date()
            else:  # string or unknown type
                return value.rstrip()  # Remove trailing spaces for string fields
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error converting field '{field['name']}': {str(e)}")
    
    def _validate_adf_record(self, record: Dict[str, Any]) -> None:
        """Validate ADF-specific record requirements."""
        # Validate record code
        if record['record_code'] not in ['0', '1', '7']:
            raise ValueError(f"Invalid record code: {record['record_code']}")
        
        # Validate BSB number format (XX-XXXX)
        bsb = record['bsb_number']
        if not re.match(r'^\d{6}$', bsb):
            raise ValueError(f"Invalid BSB number format: {bsb}")
        
        # Validate amount (must be numeric and positive)
        if record['amount'] < 0:
            raise ValueError(f"Amount must be positive: {record['amount']}")
    
    def convert_file(self, input_file: Path, output_file: Path) -> None:
        """
        Convert flat file to CSV format.
        
        Args:
            input_file: Path to the input flat file
            output_file: Path to the output CSV file
        """
        # Read the entire file
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        # Parse each line according to field specifications
        data = []
        total_amount = 0
        record_count = 0
        
        for line_num, line in enumerate(lines, 1):
            # Skip empty lines
            if not line.strip():
                continue
                
            # Validate line length
            if len(line.rstrip('\n')) != self.spec['record_length']:
                raise ValueError(
                    f"Line {line_num}: Expected length {self.spec['record_length']}, "
                    f"got {len(line.rstrip('\n'))}"
                )
            
            row = {}
            position = 0
            for field in self.spec['fields']:
                field_name = field['name']
                field_length = field['length']
                field_value = line[position:position + field_length]
                row[field_name] = self._convert_field_value(field_value, field)
                position += field_length
            
            # Perform ADF-specific validations
            if self.spec['name'] == 'adf':
                self._validate_adf_record(row)
                if row['record_code'] == '1':  # Detail record
                    total_amount += row['amount']
                    record_count += 1
            
            data.append(row)
        
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        
        # Print summary for ADF files
        if self.spec['name'] == 'adf':
            print(f"\nADF File Summary:")
            print(f"Total Records: {record_count}")
            print(f"Total Amount: ${total_amount:,.2f}") 