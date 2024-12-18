# SAP Tables Extractor

A Python tool that extracts SAP table information and their field definitions from SAP documentation sources. The tool uses DSPy and Google's Gemini AI to process and structure the information into JSON files.

## Overview

This tool automatically extracts:
- SAP table definitions
- Field information for each table
- Technical details and metadata
- Relationships and dependencies

## Features

### Table Information Extracted
- Table name and number
- Table description
- Table category (TRANSP, POOL, etc.)
- Delivery class
- All fields and their properties

### Field Details Include
- Field name
- Key field indicator
- Data Element information
- Domain details
- Data Type
- Length
- Decimals
- Short Description

## Requirements

### Python Dependencies 
bash
dspy-ai
beautifulsoup4
aiohttp
python-dotenv
google-generativeai


### API Keys
Create a `.env` file with:

env
GOOGLE_API_KEY=your_gemini_api_key_here


## Installation

1. Clone the repository
2. Install dependencies:

bash
pip install -r requirements.txt


## Usage

Run the main script:

bash
python sap_tables_agent_web.py


The script will:
1. Extract SAP table information
2. Process field definitions
3. Generate JSON files in the `sap_tables` directory

## Output

### Directory Structure

sap_tables/
├── A000.json
├── A001.json
├── A008.json
├── A009.json
└── ...


### JSON Format

json
{
"number": "001",
"name": "TABLE_NAME",
"description": "Table Description",
"category": "TRANSP",
"delivery_class": "A",
"fields": [
{
"field": "FIELD_NAME",
"key": "X",
"data_element": {
"name": "ELEMENT_NAME",
"url": "documentation_url"
},
"domain": {
"name": "DOMAIN_NAME",
"url": "documentation_url"
},
"data_type": "CHAR",
"length": "10",
"decimals": "0",
"short_description": "Field Description"
}
]
}


## Testing

Run the test suite:
bash
python -m unittest test_sap_tables_agent_web.py


## Error Handling

The tool includes:
- Network error handling
- File system error management
- Data validation
- Detailed logging

## Limitations

- Limited to 10 tables by default
- Requires internet connection
- Depends on source website availability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License

---
Created by [CherryVanillaa](https://github.com/cherryvanillaa)
