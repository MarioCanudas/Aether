import re

# Regex pattern for extracting the transaction details
pattern = re.compile(
    r'(?P<date>\d{2}-\w{3}-\d{2})'                              # Date (e.g., 01-AGO-24)
    r'(?P<description>.+?)(?=\d{1,3}(?:,\d{3})*(?:\.\d{2}))'     # Description (until the next number that looks like an amount)
    r'(?P<amount1>\d{1,3}(?:,\d{3})*(?:\.\d{2}))'                # First amount (income or withdrawal)
)
