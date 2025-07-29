import pandas as pd
import numpy as np
import re
from sklearn.cluster import KMeans
from functools import cache
from typing import List, Tuple, Dict, Any
from ..core import Reconstructor
from utils import classify_words, identify_date_separator
from models.amounts import AmountColumns
from models.delimitations import ColumnDelimitations
from models.tables import ReconstructedTable

class TableReconstructor(Reconstructor):
    @cache
    def get_classified_rows(self) -> pd.DataFrame:
        """Classifies each word from the grouped rows into date, description or amount columns"""
        # Get the grouped rows DataFrame to process each row of detected words
        grouped_rows = self.grouped_rows.df
        
        # Retrieve statement properties, including date and amount column patterns
        date_pattern = self.bank_properties.date_pattern
        all_amount_columns = self.bank_properties.amount_columns.all_list
        
        reconstructed_table = []
        
        # Iterate over each grouped row to classify its words
        for _, row in grouped_rows.iterrows():
            # Initialize the row structure depending    on the number of amount columns
            if len(all_amount_columns) > 1:
                current_row = {'date': None, 'description': '', 'amount': []}
            else:
                current_row = {'date': None, 'description': '', 'amount': None}
            
            # For each word in the row, classify as date, amount, or description
            for text, x0, _ in row['words']:
                classification = classify_words(date_pattern, text)
                
                # Assign the word to the appropriate field based on its classification
                if classification == 'date' and not current_row['date']:
                    current_row['date'] = text
                elif classification == 'amount':
                    if len(all_amount_columns) > 1:
                        # For multiple amount columns, store both value and position
                        current_row['amount'].append((text, x0))
                    else:
                        # For a single amount column, just store the value
                        current_row['amount'] = text
                elif classification == 'description':
                    # Concatenate description words
                    current_row['description'] += text + " "
            
            # If no amount was found, set to None for consistency
            if not current_row['amount']:
                current_row['amount'] = None
            reconstructed_table.append(current_row)
        
        # Return the reconstructed table as a DataFrame
        if reconstructed_table:
            return pd.DataFrame(reconstructed_table) 
        else:
            return pd.DataFrame(columns= ['date', 'description', 'amount'])
    
    @staticmethod
    def get_amount_columns_centroids(column_delimitation: ColumnDelimitations, amount_columns: AmountColumns) -> np.array:
        """
        Get the centroids of the amount columns, based on the column delimitation of the amount columns.
        
        The centroids are calculated as the average of the x0 and x1 positions of the column delimitation.
        
        Returns:
            np.array: The centroids of the amount columns.
        """
        # Get the column delimitation information (column names and their x0, x1 positions)
        columns = column_delimitation.columns
        x0_list = column_delimitation.x0
        x1_list = column_delimitation.x1
        
        centroids = []
        
        # Iterate over all columns to find those that are amount columns
        for i, col in enumerate(columns):
            if col in amount_columns.all_list:
                # Calculate the centroid as the average of x0 and x1 for the column
                centroid = (x0_list[i] + x1_list[i]) / 2
                centroids.append(centroid)
        
        # Return the centroids as a numpy array with shape (n, 1)
        return np.array(centroids).reshape(-1, 1)
    
    @staticmethod
    def filter_amounts_by_alignment(classified_rows: pd.DataFrame, column_centroids: np.array) -> Tuple[List[float], List[Tuple[int, str]]]:
        """
        Filters amounts that are horizontally aligned with known amount column positions.
        Returns their x-coordinates and row references for clustering.
        """
        all_x0 = []
        row_indices = []
        tolerance = 25 # pixels
        
        # Check each row for amounts that align with column centroids
        for i, row in classified_rows.iterrows():
            if row['amount'] and isinstance(row['amount'], list):
                for amount, x0 in row['amount']:
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
    def cluster_amounts_columns(all_x0: List[float], column_centroids: np.array, amount_columns: AmountColumns) -> Tuple[np.array, dict]:
        """
        Clusters the amounts into their respective columns using K-means clustering on x-coordinates.
        
        Args:
            all_x0 (List[float]): The x-coordinates of the amounts.
            column_centroids (np.array): The centroids of the amount columns.
            amount_columns (List[str]): The names of the amount columns.
            
        Returns:
            Tuple[np.array, dict]: The clusters and the mapping of clusters to column names.
        """
        all_amount_columns = amount_columns.all_list
        n_amount_columns = len(all_amount_columns)
        
        X = np.array(all_x0).reshape(-1, 1)
        kmeans = KMeans(n_clusters=n_amount_columns, init=column_centroids, n_init=1)
        clusters = kmeans.fit_predict(X)
        
        # Map clusters to column names based on horizontal position
        final_centroids = kmeans.cluster_centers_.flatten()
        sorted_cluster_indices = np.argsort(final_centroids)
        cluster_to_column = {sorted_cluster_indices[i]: all_amount_columns[i] for i in range(n_amount_columns)}
        
        return clusters, cluster_to_column
        
    @cache
    def get_structured_table(self) -> ReconstructedTable:
        """
        Structures amounts into their respective columns using K-means clustering on x-coordinates.
        For single amount column, maps directly. For multiple columns, clusters by position.
        """
        classified_rows = self.get_classified_rows()
        amount_columns = self.bank_properties.amount_columns
        
        # Simple case: single amount column
        if amount_columns.is_mono_column:
            df = classified_rows.rename(columns={'amount': amount_columns.column})
            return ReconstructedTable(df= df, amount_columns= amount_columns)
        
        # Complex case: multiple amount columns - use clustering        
        column_centroids = self.get_amount_columns_centroids(self.column_delimitation, amount_columns)
        all_x0, row_indices = self.filter_amounts_by_alignment(classified_rows, column_centroids)
        clusters, cluster_to_column = self.cluster_amounts_columns(all_x0, column_centroids, amount_columns)
        
        # Assign amounts to their respective columns
        result_df = classified_rows.copy()
        for col in amount_columns.all_list:
            result_df[col] = ""
        
        for i, (row_idx, amount_text) in enumerate(row_indices):
            cluster = clusters[i]
            column_name = cluster_to_column[cluster]
            if result_df.loc[row_idx, column_name] == "":
                result_df.loc[row_idx, column_name] = amount_text
                
        df = result_df.drop('amount', axis=1)
        
        return ReconstructedTable(df= df, amount_columns= amount_columns)
    
    def correct_date_errors(self, merged_rows: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Corrects date errors in the reconstructed table.
        """
        date_groups = self.bank_properties.date_groups
        day_group = date_groups.day
        month_group = date_groups.month
        year_group = date_groups.year
        
        if year_group is None:
            return pd.DataFrame(merged_rows)
        
        month_pattern = self.bank_properties.month_pattern
        date_pattern = re.compile(self.bank_properties.date_pattern)
        date_separator = identify_date_separator(date_pattern)
        
        rows_to_delete = []
        
        for i, row in enumerate(merged_rows):
            date = row['date']
            match = date_pattern.match(date)
            
            if not match:
                rows_to_delete.append(i)
                continue

            day = match.group(day_group)
            month = match.group(month_group)
            year = match.group(year_group)
            
            if not year:
                date_order = [None, None, None]
                date_order[day_group - 1] = day
                date_order[month_group - 1] = month
                
                no_date_word = ' '.join(date.split(date_separator)[year_group - 1:])
                
                for j in range(len(merged_rows)):
                    j_date: str = merged_rows[j]['date']
                    j_date_month: str = date_pattern.match(j_date).group(month_group)
                    j_date_year: str = date_pattern.match(j_date).group(year_group)
                    
                    if j_date_month == month and j_date_year.isdigit():
                        date_order[year_group - 1] = j_date_year
                        break
                else:
                    jan = month_pattern.keys()[0]
                    dic = month_pattern.keys()[-1]
                    relative_year = None
                    relative_month = None
                    
                    for j in range(len(merged_rows)):
                        j_date: str = merged_rows[j]['date']
                        j_date_month: str = date_pattern.match(j_date).group(month_group)
                        j_date_year: str = date_pattern.match(j_date).group(year_group)
                        
                        if j_date_year.isdigit():
                            relative_year = j_date_year
                            relative_month = j_date_month
                            break
                        
                    if month == jan and relative_month == dic:
                        date_order[year_group - 1] = int(relative_year) + 1
                    elif month == dic and relative_month == jan:
                        date_order[year_group - 1] = int(relative_year) - 1
                    else:
                        date_order[year_group] = relative_year
                
                merged_rows[i]['date'] = date_separator.join(date_order)
                merged_rows[i]['description'] = no_date_word.strip() + merged_rows[i]['description']
                
        return pd.DataFrame(merged_rows).drop(rows_to_delete).reset_index(drop=True)
    
    def reconstruct_table(self) -> ReconstructedTable:
        """
        Merges multi-line transactions into single rows and filters out invalid entries.
        Combines description fragments and fills missing amounts from continuation rows.
        """
        df_structured = self.get_structured_table()
        amount_columns = df_structured.amount_columns
        all_amount_columns = amount_columns.all_list
        
        if df_structured.empty:
            raise ValueError("The structured table is empty")
        
        merged_rows = []
        current_row = None
        
        date_pattern = self.bank_properties.date_pattern

        # Merge rows that belong to the same transaction
        for _, row in df_structured.iterrows():
            try:
                if row['date'] is not None:  # New transaction starts
                    if current_row is not None:
                        merged_rows.append(current_row)
                    current_row = row.copy()
                else:  # Continuation of current transaction
                    # Fill missing amounts from continuation rows
                    for col in all_amount_columns:
                        if (row[col] != '' or row[col] is not None) and (current_row[col] == '' or current_row[col] is None):
                            current_row[col] = row[col]
                    # Append description fragments
                    try:
                        current_row['description'] += " " + row['description'] + " "
                    except:
                        continue
            except TypeError:
                continue

        if current_row is not None:
            merged_rows.append(current_row)

        # Filter out rows without amounts and invalid dates
        df_merged = self.correct_date_errors(merged_rows)
        df_merged = df_merged[~df_merged.apply(lambda row: all(pd.isna(row[col]) or row[col] == '' for col in all_amount_columns), axis=1)]
        
        df_filtered = df_merged[df_merged['date'].str.match(date_pattern, na=False)].reset_index(drop=True)
        
        return ReconstructedTable(df= df_filtered, amount_columns= amount_columns)