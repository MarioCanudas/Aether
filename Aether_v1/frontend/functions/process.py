import re
import os
import pdfplumber
import pandas as pd
from functions.pattern import pattern
from io import BytesIO

# Create a mapping for Spanish month abbreviations
month_map = {
    'ENE': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'ABR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
    'JUL': 'Jul', 'AGO': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DIC': 'Dec'
}

# Function to replace Spanish month abbreviations with English
def replace_spanish_month(date_str):
    """
    Replace Spanish month abbreviations with English ones in the date string.
    """
    for spanish, english in month_map.items():
        date_str = date_str.replace(spanish, english)
    return date_str

# Function to extract text from all pages in a PDF file
def extract_text_from_pdf(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page_number in range(len(pdf.pages)):
            page_text = pdf.pages[page_number].extract_text()
            full_text += page_text + "\n"
    return full_text

# Function to extract transaction data from the PDF text
def extract_transactions_from_text(pdf_text, pattern):
    matches = pattern.finditer(pdf_text)
    return matches

# Function to extract the balance from the next line if missing
def extract_balance(line):
    balance_pattern = re.compile(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})')
    match = balance_pattern.search(line)
    if match:
        return float(match.group().replace(',', ''))
    return None

# Function to classify the transaction as income or withdrawal
def classify_transaction(description, amount1):
    clean_amount = amount1.replace(',', '')
    income_keywords = ['RECIBIDO', 'CHEQUE', 'DEPOSITO', 'TRANSFERENCIA', 'TRASPASO']
    forced_withdrawal_keywords = ['PAGO REFERENCIADO', 'IMPUESTO']

    if any(keyword in description.upper() for keyword in forced_withdrawal_keywords):
        return 0, float(clean_amount)  # Forced withdrawal
    elif any(keyword in description.upper() for keyword in income_keywords):
        return float(clean_amount), 0  # Income
    else:
        return 0, float(clean_amount)  # Default to withdrawal

# Function to process each match and find the balance on the next line if missing
def process_transaction_match(match, pdf_text, start_index):
    date = match.group('date')
    description = match.group('description').strip()
    amount1 = match.group('amount1')

    # Try to get the next line (balance might be on the next line)
    next_line_index = start_index + len(match.group(0))
    remaining_text = pdf_text[next_line_index:].split('\n', 1)

    balance_line = remaining_text[0] if remaining_text else ""
    balance = extract_balance(balance_line)

    if balance is None:
        balance = 0.0

    income, withdrawal = classify_transaction(description, amount1)

    return {
        'Date': date,
        'Description': description,
        'Income': income,
        'Withdrawal': withdrawal,
        'Balance': balance
    }

def update_saldo_anterior(processed_data):
    processed_data.loc[
        (processed_data['Description'] == 'SALDO ANTERIOR') & (processed_data['Income'] == 0),
        'Balance'
    ] = processed_data['Withdrawal']
    processed_data.loc[processed_data['Description'] == 'SALDO ANTERIOR', 'Withdrawal'] = 0
    processed_data.loc[processed_data['Description'] == 'SALDO ANTERIOR', 'Date'] = (
        processed_data.loc[processed_data['Description'] == 'SALDO ANTERIOR', 'Date'] + pd.DateOffset(days=1)
    )
    return processed_data

# Function to process the entire folder and extract transactions into a CSV and DataFrame
def process_pdf_folder(folder_path, output_csv):
    transactions = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            pdf_text = extract_text_from_pdf(pdf_path)
            lines = pdf_text.split('\n')

            for line in lines:
                if "Inversión Enlace Personal" in line:
                    break

                matches = extract_transactions_from_text(line, pattern)

                for match in matches:
                    start_index = pdf_text.find(match.group(0))
                    transaction = process_transaction_match(match, pdf_text, start_index)
                    transactions.append(transaction)

    processed_data = pd.DataFrame(transactions)
    processed_data.fillna(0, inplace=True)

    # Replace Spanish month abbreviations and convert 'Date' column to datetime
    processed_data['Date'] = processed_data['Date'].apply(lambda x: replace_spanish_month(x))
    processed_data['Date'] = pd.to_datetime(processed_data['Date'], format='%d-%b-%y', dayfirst=True)

    # Sort data
    processed_data.sort_values(by=['Date', 'Description'], inplace=True)
    processed_data = update_saldo_anterior(processed_data)

    processed_data.to_csv(output_csv, index=False)
    print(f"\nData exported successfully to: {output_csv}")

    return processed_data

def process_pdf_bytes(uploaded_file):
    transactions = []
    with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
        pdf_text = ""
        for page in pdf.pages:
            pdf_text += page.extract_text() + "\n"

        lines = pdf_text.split('\n')

        for line in lines:
            if "Inversión Enlace Personal" in line:
                break

            matches = extract_transactions_from_text(line, pattern)

            for match in matches:
                start_index = pdf_text.find(match.group(0))
                transaction = process_transaction_match(match, pdf_text, start_index)
                transactions.append(transaction)

    processed_data = pd.DataFrame(transactions)
    processed_data.fillna(0, inplace=True)

    # Replace Spanish month abbreviations and convert 'Date' column to datetime
    processed_data['Date'] = processed_data['Date'].apply(lambda x: replace_spanish_month(x))
    processed_data['Date'] = pd.to_datetime(processed_data['Date'], format='%d-%b-%y', dayfirst=True)

    processed_data.sort_values(by=['Date', 'Description'], inplace=True)
    processed_data = update_saldo_anterior(processed_data)

    return processed_data
