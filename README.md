# Aether_v1

Aether_v1 is a Python project that processes bank statements (PDFs) and extracts transactions, saving them in a CSV file. The current version of the project processes a sample bank statement from **NuBank** in Spanish and extracts transactions for multiple months.

## Table of Contents

- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [How to Run](#how-to-run)
  - [1. Input File](#1-input-file)
  - [2. Run the Script](#2-run-the-script)
  - [3. Output](#3-output)
- [Example Output](#example-output)
- [Project Features](#project-features)
- [Project Expansion](#project-expansion)
- [License](#license)

---

## Project Structure

The project is organized into several folders, each with a specific responsibility:
```bash
/Aether_v1
│
├── /config               # Configuration settings (e.g., paths, constants)
├── /core                 # Core functionalities, including abstract classes
├── /documents            # Folder for input and output documents
│   ├── /inputs           # Input files (e.g., PDF statements)
│   │   └── /test_files   # Test files (e.g., nu_bank_statement.pdf)
│   └── /outputs          # Output folder where CSV files will be saved
├── /frontend             # Streamlit front end for the app
│   ├── /assets           # Static files, such as images
│   ├── /functions        # Utility functions for Streamlit pages
│   └── /views            # Separate folder for each page
│       ├── data.py       # Data export page
│       ├── expenses_analysis.py # Expenses analysis page
│       ├── home.py       # Home page (file upload, initial analysis)
│       ├── income_analysis.py # Income analysis page
│       └── app.py        # Main Streamlit app setup
├── /models               # Models for transaction extraction per bank
├── /scripts              # Executable scripts (e.g., to process transactions)
├── /utils                # Utility functions used across the project
├── process_transactions.py # Main script to process bank statements
├── .gitignore            # Files and directories ignored by Git
└── README.md             # Project documentation (this file)
```
---

## Requirements

To run the project, you'll need to have Python 3 installed. You will also need the following Python libraries:

- `fitz` (from `PyMuPDF`)
- `re` (built-in Python library)
- `pandas`

To install these dependencies, use the following command:

pip install pymupdf pandas
## How to Run
Follow these steps to process the bank statement and generate a CSV file with the transactions.

### 1. Input File
The project processes a NuBank statement (nu_bank_statement.pdf), which is located in the /documents/inputs/test_files/ folder. It extracts transactions for January (ENE) and February (FEB).

### 2. Run the Script
To process the PDF and generate the CSV, run the process_transactions.py script:

python3 process_transactions.py
This will extract the transactions and generate the output in CSV format.

### 3. Output
Once the script is executed, a CSV file containing the extracted transactions will be saved in the /documents/outputs/ folder. The CSV will include details such as the date, category, description, and amount of each transaction.

### 4. streamlit
Run the Streamlit App: Navigate to the frontend directory and start the app:

```python
streamlit run app.py
```
Access the App: After starting, open your web browser and go to the URL provided by Streamlit (usually http://localhost:8501).

## Example Output
The generated CSV file will have the following structure:

Date,Category,Description,Amount
06 ENE,Others,Pago a tu tarjeta de crédito,-$10,400.00
09 ENE,Others,Web Transfer Vision Cr,$400.00
01 FEB,Service,Amazon Mx,$508.95
04 FEB,Restaurant,Top Bar - Chintz,$142.38
...
## Project Features
PDF Parsing: Extracts transaction details from PDF bank statements in Spanish.
Multi-Month Support: Processes transactions for multiple months (e.g., January and February).
CSV Export: Saves extracted transaction data into a CSV file for easy reporting and analysis.
## Project Expansion
The project is designed for easy extensibility. To add support for other banks:

Update or add models in the /models directory.
Modify the transaction extraction logic to handle the specific format of the new bank statements.
## License
This project is licensed under the MIT License.

vbnet
Copy code

### Conclusion:
This Markdown structure provides a clean and organized way to document your project. It is detailed enough for new users to understand how to set up, run, and expand the project, while also providing clear instructions on the requirements and expected output.
