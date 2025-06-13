import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from functools import cache
from typing import List, Tuple
from ..core import Reconstructor
from utils import classify_words

class TableReconstructor(Reconstructor):
    def classify_columns(self) -> pd.DataFrame:
        # Get the grouped rows DataFrame to process each row of detected words
        df_structured = self.grouped_rows
        
        # Retrieve statement properties, including date and amount column patterns
        date_pattern = self.statement_properties['date_pattern']
        amount_columns = self.statement_properties['amount_column']
        
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
                classification = classify_words(date_pattern, text)
                
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
    
    @staticmethod
    def get_amount_columns_centroids(delimitation: dict, amount_columns: List[str]) -> np.array:
        """
        Get the centroids of the amount columns, based on the column delimitation of the amount columns.
        
        The centroids are calculated as the average of the x0 and x1 positions of the column delimitation.
        
        Returns:
            np.array: The centroids of the amount columns.
        """
        # Get the column delimitation information (column names and their x0, x1 positions)
        columns = delimitation['column']
        x0_list = delimitation['x0']
        x1_list = delimitation['x1']
        
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
    
    @staticmethod
    def cluster_amounts_columns(all_x0: List[float], column_centroids: np.array, amount_columns: List[str]) -> Tuple[np.array, dict]:
        """
        Clusters the amounts into their respective columns using K-means clustering on x-coordinates.
        
        Args:
            all_x0 (List[float]): The x-coordinates of the amounts.
            column_centroids (np.array): The centroids of the amount columns.
            amount_columns (List[str]): The names of the amount columns.
            
        Returns:
            Tuple[np.array, dict]: The clusters and the mapping of clusters to column names.
        """
        n_amount_columns = len(amount_columns)
        
        X = np.array(all_x0).reshape(-1, 1)
        kmeans = KMeans(n_clusters=n_amount_columns, init=column_centroids, n_init=1)
        clusters = kmeans.fit_predict(X)
        
        # Map clusters to column names based on horizontal position
        final_centroids = kmeans.cluster_centers_.flatten()
        sorted_cluster_indices = np.argsort(final_centroids)
        cluster_to_column = {sorted_cluster_indices[i]: amount_columns[i] for i in range(n_amount_columns)}
        
        return clusters, cluster_to_column
        
    @cache
    def get_structured_table(self) -> pd.DataFrame:
        """
        Structures amounts into their respective columns using K-means clustering on x-coordinates.
        For single amount column, maps directly. For multiple columns, clusters by position.
        """
        classified_columns = self.classify_columns()
        amount_columns = self.statement_properties['amount_column']
        n_amount_columns = len(amount_columns)
        
        # Simple case: single amount column
        if n_amount_columns == 1:
            amount_column = amount_columns[0]
            
            return classified_columns.rename(columns={'Amount': amount_column})
        
        # Complex case: multiple amount columns - use clustering        
        column_centroids = self.get_amount_columns_centroids(self.column_delimitation, amount_columns)
        all_x0, row_indices = self.filter_amounts_by_alignment(classified_columns, column_centroids)
        clusters, cluster_to_column = self.cluster_amounts_columns(all_x0, column_centroids, amount_columns)
        
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
        
        amount_columns = self.statement_properties['amount_column']
        date_pattern = self.statement_properties['date_pattern']

        # Merge rows that belong to the same transaction
        for _, row in df_structured.iterrows():
            try:
                if row['Date'] is not None:  # New transaction starts
                    if current_row is not None:
                        merged_rows.append(current_row)
                    current_row = row.copy()
                else:  # Continuation of current transaction
                    # Fill missing amounts from continuation rows
                    for col in amount_columns:
                        if (row[col] != '' or row[col] is not None) and (current_row[col] == '' or current_row[col] is None):
                            current_row[col] = row[col]
                    # Append description fragments
                    try:
                        current_row['Description'] += " " + row['Description'] + " "
                    except:
                        continue
            except TypeError:
                continue

        if current_row is not None:
            merged_rows.append(current_row)

        # Filter out rows without amounts and invalid dates
        df_merged = pd.DataFrame(merged_rows)
        df_merged = df_merged[~df_merged.apply(lambda row: all(pd.isna(row[col]) or row[col] == '' for col in amount_columns), axis=1)]
        
        return df_merged[df_merged['Date'].str.match(date_pattern, na=False)].reset_index(drop=True)