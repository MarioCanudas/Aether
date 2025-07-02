from core import TableReconstructor
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import re
from functools import cache
from typing import List, Tuple, Literal

def is_amount(value: str) -> bool:
    # Ignore the empty strings
    if value == '':
        return True
    
    amount_pattern = r'^[+-]?\$?[+-]?(0|[1-9]\d{0,2}(?:,\d{3})*)\.\d{2}[-+]?$'

    return bool(re.match(amount_pattern, value.strip()))

class TransactionTableReconstructor(TableReconstructor):
    @staticmethod
    def classify_words(date_pattern: str, text: str) -> Literal['date', 'amount', 'description']:
        """
        Classifies a word into a category based on its content, based on the date pattern and the amount pattern.
        
        Args:
            date_pattern (str): The pattern to match dates.
            text (str): The word to classify.
            
        Returns:
            str: The category of the word.
        """
        if re.match(date_pattern, text):
            return 'date'
        elif is_amount(text):
            return 'amount'
        else:
            return 'description'
    
    def classify_columns(self) -> pd.DataFrame:
        # Get the grouped rows DataFrame to process each row of detected words
        df_structured = self.grouped_rows
        
        # Retrieve statement properties, including date and amount column patterns
        statement_properties = self.bank_detector.get_statement_properties()
        date_pattern = statement_properties['date_pattern']
        amount_columns = statement_properties['amount_column']
        
        reconstructed_table = []
        
        # Iterate over each grouped row to classify its words
        for _, row in df_structured.iterrows():
            # Initialize the row structure depending on the number of amount columns
            if len(amount_columns) > 1:
                current_row = {'Date': None, 'Description': '', 'Amount': []}
            else:
                current_row = {'Date': None, 'Description': '', 'Amount': None}
            
            # For each word in the row, classify as date, amount, or description
            for text, x0, _ in row['words']:
                classification = self.classify_words(date_pattern, text)
                
                # Assign the word to the appropriate field based on its classification
                if classification == 'date' and not current_row['Date']:
                    current_row['Date'] = text
                elif classification == 'amount':
                    if len(amount_columns) > 1:
                        # For multiple amount columns, store both value and position
                        current_row['Amount'].append((text, x0))
                    else:
                        # For a single amount column, just store the value
                        current_row['Amount'] = text
                elif classification == 'description':
                    # Concatenate description words
                    current_row['Description'] += text + " "
            
            # If no amount was found, set to None for consistency
            if not current_row['Amount']:
                current_row['Amount'] = None
            reconstructed_table.append(current_row)
        
        # Return the reconstructed table as a DataFrame
        return pd.DataFrame(reconstructed_table) 
    
    @cache
    def get_amount_columns_centroids(self) -> np.array:
        """
        Get the centroids of the amount columns, based on the column delimitation of the amount columns.
        
        The centroids are calculated as the average of the x0 and x1 positions of the column delimitation.
        
        Returns:
            np.array: The centroids of the amount columns.
        """
        # Get the column delimitation information (column names and their x0, x1 positions)
        delimitation = self.column_delimitation
        columns = delimitation['column']
        x0_list = delimitation['x0']
        x1_list = delimitation['x1']
        
        # Get the list of amount columns from the statement properties
        statement_properties = self.bank_detector.get_statement_properties()
        amount_columns = statement_properties['amount_column']
        
        centroids = []
        
        # Iterate over all columns to find those that are amount columns
        for i, col in enumerate(columns):
            if col in amount_columns:
                # Calculate the centroid as the average of x0 and x1 for the column
                centroid = (x0_list[i] + x1_list[i]) / 2
                centroids.append(centroid)
        
        # Return the centroids as a numpy array with shape (n, 1)
        return np.array(centroids).reshape(-1, 1)
    
    @staticmethod
    def filter_amounts_by_alignment(classified_columns: pd.DataFrame, column_centroids: np.array) -> Tuple[List[float], List[Tuple[int, str]]]:
        """
        Filters amounts that are horizontally aligned with known amount column positions.
        Returns their x-coordinates and row references for clustering.
        """
        all_x0 = []
        row_indices = []
        tolerance = 25 # pixels
        
        # Check each row for amounts that align with column centroids
        for i, row in classified_columns.iterrows():
            if row['Amount'] and isinstance(row['Amount'], list):
                for amount, x0 in row['Amount']:
                    # Check if amount position is within tolerance of any column centroid
                    is_near_column = any(
                        abs(x0 - centroid[0]) <= tolerance 
                        for centroid in column_centroids
                    )
                    
                    if is_near_column:
                        all_x0.append(x0)
                        row_indices.append((i, amount))
        
        return all_x0, row_indices
    
    @cache
    def get_structured_table(self) -> pd.DataFrame:
        """
        Structures amounts into their respective columns using K-means clustering on x-coordinates.
        For single amount column, maps directly. For multiple columns, clusters by position.
        """
        classified_columns = self.classify_columns()
        statement_properties = self.bank_detector.get_statement_properties()
        amount_columns = statement_properties['amount_column']
        n_amount_columns = len(amount_columns)
        
        # Simple case: single amount column
        if n_amount_columns == 1:
            amount_column = amount_columns[0]
            classified_columns[amount_column] = classified_columns['Amount']
            classified_columns = classified_columns.drop('Amount', axis=1)
            return classified_columns
        
        # Complex case: multiple amount columns - use clustering        
        column_centroids = self.get_amount_columns_centroids()
        all_x0, row_indices = self.filter_amounts_by_alignment(classified_columns, column_centroids)
        
        # Cluster amount positions using K-means
        X = np.array(all_x0).reshape(-1, 1)
        kmeans = KMeans(n_clusters=n_amount_columns, init=column_centroids, n_init=1)
        clusters = kmeans.fit_predict(X)
        
        # Map clusters to column names based on horizontal position
        final_centroids = kmeans.cluster_centers_.flatten()
        sorted_cluster_indices = np.argsort(final_centroids)
        cluster_to_column = {sorted_cluster_indices[i]: amount_columns[i] for i in range(n_amount_columns)}
        
        # Assign amounts to their respective columns
        result_df = classified_columns.copy()
        for col in amount_columns:
            result_df[col] = ""
        
        for i, (row_idx, amount_text) in enumerate(row_indices):
            cluster = clusters[i]
            column_name = cluster_to_column[cluster]
            if result_df.loc[row_idx, column_name] == "":
                result_df.loc[row_idx, column_name] = amount_text
        
        return result_df.drop('Amount', axis=1)
    
    def reconstruct_table(self) -> pd.DataFrame:
        """
        Merges multi-line transactions into single rows and filters out invalid entries.
        Combines description fragments and fills missing amounts from continuation rows.
        """
        df_structured = self.get_structured_table()
        
        merged_rows = []
        current_row = None
        
        statement_properties = self.bank_detector.get_statement_properties()
        amount_columns = statement_properties['amount_column']
        date_pattern = statement_properties['date_pattern']

        # Merge rows that belong to the same transaction
        for _, row in df_structured.iterrows():
            if row['Date'] is not None:  # New transaction starts
                if current_row is not None:
                    merged_rows.append(current_row)
                current_row = row.copy()
            else:  # Continuation of current transaction
                # Fill missing amounts from continuation rows
                for col in amount_columns:
                    if row[col] != '' and current_row[col] == '':
                        current_row[col] = row[col]
                # Append description fragments
                try:
                    current_row['Description'] += " " + row['Description'] + " "
                except:
                    continue

        if current_row is not None:
            merged_rows.append(current_row)

        # Filter out rows without amounts and invalid dates
        df_merged = pd.DataFrame(merged_rows)
        df_merged = df_merged[~df_merged.apply(lambda row: all(pd.isna(row[col]) or row[col] == '' for col in amount_columns), axis=1)]
        
        return df_merged[df_merged['Date'].str.match(date_pattern, na=False)].reset_index(drop=True)