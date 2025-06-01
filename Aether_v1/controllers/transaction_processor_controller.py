import pandas as pd
from io import BytesIO
import streamlit as st
import os
import matplotlib.pyplot as plt
from new_model import (
    PDFReader, 
    DefaultBankDetector, 
    TransactionTableBoundaryDetector, 
    TransactionRowSegmenter, 
    TransactionTableReconstructor, 
    TransactionTableNormalizer
)
from utils.helper_functions import calculate_savings_and_validate_balances, delete_double_transactions

class TransactionProcessorController:
    def initialize_session_state(self):
        if 'all_transactions' not in st.session_state:
            st.session_state.all_transactions = []
            
        if 'all_processed_data' not in st.session_state:
            st.session_state.all_processed_data = pd.DataFrame()

        if 'all_monthly_results' not in st.session_state:
            st.session_state.all_monthly_results = pd.DataFrame()
            
        if 'files_uploaded' not in st.session_state:
            st.session_state.files_uploaded = False
            
    def reset_session_state(self):
        st.session_state.all_transactions = []
        st.session_state.all_processed_data = pd.DataFrame()
        st.session_state.all_monthly_results = pd.DataFrame()
        st.session_state.files_uploaded = False
    
    def process_transactions(self, bank_detector: DefaultBankDetector) -> pd.DataFrame:
        reader = bank_detector.document_reader
        
        boundary_detector = TransactionTableBoundaryDetector(bank_detector)
        if boundary_detector.start_idx is None or boundary_detector.end_idx is None:
            bank_detector = DefaultBankDetector(reader, new_credit_format=True)
            boundary_detector = TransactionTableBoundaryDetector(bank_detector)
        df_table = boundary_detector.get_filtered_table_words()
        
        row_segmenter = TransactionRowSegmenter(df_table, bank_detector)
        column_delimitation = row_segmenter.delimit_column_positions()
        grouped_rows = row_segmenter.group_rows()

        table_reconstructor = TransactionTableReconstructor(grouped_rows, column_delimitation, bank_detector)
        df_structured = table_reconstructor.reconstruct_table()

        table_normalizer = TransactionTableNormalizer(df_structured, bank_detector)
        
        return table_normalizer.normalize_table()
    
    def process_uploaded_files(self, uploaded_files: list[BytesIO]) -> None:
        for uploaded_file in uploaded_files:
            # Check if file was already processed (using name as identifier)
            if any(uploaded_file.name == df['filename'].iloc[0] for df in st.session_state.all_transactions if not df.empty):
                continue
            # Save uploaded file to a temporary path for processing
            temp_file_path = os.path.join("frontend", f"temp_uploaded_{uploaded_file.name}")
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                bank_detector = DefaultBankDetector(PDFReader(temp_file_path))
                
                # Identify bank from PDF
                bank_name = bank_detector.detect_bank()
                statement_type = bank_detector.detect_statement_type()
                st.info(f"Detected bank for {uploaded_file.name}: {bank_name} - {statement_type}")

                transactions_df = self.process_transactions(bank_detector)
                transactions_df['bank'] = bank_name
                transactions_df['statement_type'] = statement_type
                transactions_df['filename'] = uploaded_file.name
                st.session_state.all_transactions.append(transactions_df)
            except ValueError as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
            except Exception as e:
                st.error(f"An unexpected error processing {uploaded_file.name}: {e}")

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    def get_combined_df(self) -> pd.DataFrame:
        if st.session_state.all_transactions:
            df = pd.concat(st.session_state.all_transactions, ignore_index=True)
            return df.sort_values(by='Date', ascending=True)
        else:
            return pd.DataFrame()
        
    def get_cleaned_df(self) -> pd.DataFrame:
        combined_df = self.get_combined_df()
        return delete_double_transactions(combined_df)
    
    def get_monthly_results(self) -> pd.DataFrame:
        cleaned_df = self.get_cleaned_df()
        df = calculate_savings_and_validate_balances(cleaned_df)
        return df.sort_values(by='Month', ascending=True)
    
    def update_all_processed_data(self) -> None:
        st.session_state.all_processed_data = self.get_combined_df()
        
    def update_all_monthly_results(self) -> None:
        st.session_state.all_monthly_results = self.get_monthly_results()
        
    def get_total_savings(self) -> float:
        all_monthly_results = st.session_state.all_monthly_results
        return all_monthly_results['savings'].sum()
    
    def get_avg_income_per_month(self) -> float:
        all_monthly_results = st.session_state.all_monthly_results
        return all_monthly_results['total_income'].mean()
    
    def get_avg_withdrawal_per_month(self) -> float:
        all_monthly_results = st.session_state.all_monthly_results
        return all_monthly_results['total_withdrawal'].mean()
    
    def get_plot_savings_donut_chart(self, total_savings, avg_income_per_month):
        """
        Plots a donut chart based on the savings compared to the average income.

        :param total_savings: The total savings value.
        :param avg_income_per_month: The average income per month.
        :return: A Matplotlib figure containing the donut chart and the corresponding label.
        """
        # Determine completion percentage, label, and color for the donut chart
        if total_savings >= 0.10 * avg_income_per_month:
            completion_percentage = 100
            label = "Excellent!"
            color = '#1E90FF'  # Blue
            points = '100 pts'
        elif 0 <= total_savings < 0.10 * avg_income_per_month:
            completion_percentage = 75
            label = "Good"
            color = '#4CAF50'  # Green
            points = '75 pts'
        elif -0.10 * avg_income_per_month <= total_savings < 0:
            completion_percentage = 50
            label = "Regular"
            color = '#FF9800'  # Orange
            points = '50 pts'
        else:
            completion_percentage = 25
            label = "Poor"
            color = '#F44336'  # Red
            points = '25 pts'

        # Plot the donut chart
        fig, ax = plt.subplots()
        sizes = [completion_percentage, 100 - completion_percentage]
        colors = [color, '#E0E0E0']  # Color for the completed part and light gray for the remaining part
        ax.pie(sizes, labels=['', ''], colors=colors, startangle=90, counterclock=False,
            wedgeprops=dict(width=0.3))

        # Add the label in the center of the donut
        ax.text(0, 0, points, ha='center', va='center', fontsize=14, weight='bold', color ='white')

        # Make the plot background transparent
        fig.patch.set_alpha(0)  # Make the figure's background transparent
        ax.set_aspect('equal')

        return fig, label
        
    def get_financial_tips(self, label):
        """
        Returns financial tips based on the given financial health label.

        :param label: The financial health label (e.g., "Excellent!", "Decent", "Caution", "Alert!")
        :return: A list of 3 tips specific to the financial health situation.
        """
        # Ensure that the label is lowercased and stripped of any extra spaces
        label = label.strip().lower()

        if label == "excellent!":
            return [
                "Consider investing more to grow your wealth.",
                "Maintain your current savings habits to ensure long-term financial stability.",
                "Explore tax-saving opportunities for greater efficiency."
            ]
        elif label == "good":
            return [
                "Focus on increasing your savings by cutting unnecessary expenses.",
                "Review your investment portfolio and make adjustments where needed.",
                "Set clear financial goals to improve your savings rate."
            ]
        elif label == "regular":
            return [
                "Reduce discretionary spending to improve your savings rate.",
                "Create a detailed budget and stick to it for better financial management.",
                "Consider automating your savings to avoid overspending."
            ]
        elif label == "poor":
            return [
                "Take immediate action to reduce your debt and manage your expenses.",
                "Seek professional financial advice to get back on track.",
                "Focus on building an emergency fund to improve your financial health."
            ]
        else:
            return ["No specific tips available for this financial health situation."]
        
    def clear_all_transactions(self) -> None:
        st.session_state.all_transactions = []
        st.session_state.monthly_results = pd.DataFrame()