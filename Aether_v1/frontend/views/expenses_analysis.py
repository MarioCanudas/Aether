import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def show_expenses_analysis():
    st.title('Expenses Analysis')

    # Check if monthly results are available
    if 'all_monthly_results' in st.session_state and not st.session_state.all_monthly_results.empty:
        st.write("Analysis based on monthly results")

        # Convert 'Month' to a string format for plotting
        monthly_results = st.session_state.all_monthly_results.copy()
        monthly_results['Month'] = monthly_results['Month'].astype(str)

        # Bar chart for Total Expenses
        st.subheader('Total Expenses by Month')
        fig_expenses, ax_expenses = plt.subplots()

        # Plot the data
        ax_expenses.bar(monthly_results['Month'], monthly_results['total_withdrawal'], color='orange')

        # Transparent background, Y-axis grid only, and white labels
        fig_expenses.patch.set_alpha(0)  # Transparent background
        ax_expenses.set_facecolor('none')  # Transparent axes background
        ax_expenses.grid(True, color='gray', linestyle='-', linewidth=0.5, axis='y')
        ax_expenses.set_xticklabels(monthly_results['Month'], rotation=90, color='white')
        ax_expenses.set_yticklabels(ax_expenses.get_yticks(), color='white')

        # Display the plot
        st.pyplot(fig_expenses)

        # Check if processed data is available for daily analysis
        if 'all_processed_data' in st.session_state and not st.session_state.all_processed_data.empty:
            processed_data = st.session_state.all_processed_data.copy()
            processed_data['Date'] = pd.to_datetime(processed_data['Date'])

            # Filter to keep only rows with non-zero expenses
            expenses_data = processed_data[processed_data['Withdrawal'] > 0]
            expenses_data['Day'] = expenses_data['Date'].dt.day

            # Average expenses by day of the month
            avg_expenses_per_day = expenses_data.groupby('Day')['Withdrawal'].mean().reindex(range(1, 32), fill_value=0)

            st.subheader('Average Expenses by Day')
            fig_avg_expenses_per_day, ax_avg_expenses_per_day = plt.subplots()
            ax_avg_expenses_per_day.bar(avg_expenses_per_day.index, avg_expenses_per_day, color='red')

            # Transparent background, Y-axis grid only, and white labels
            fig_avg_expenses_per_day.patch.set_alpha(0)
            ax_avg_expenses_per_day.set_facecolor('none')
            ax_avg_expenses_per_day.grid(True, color='gray', linestyle='-', linewidth=0.5, axis='y')
            ax_avg_expenses_per_day.set_xticks(range(1, 32))
            ax_avg_expenses_per_day.set_xticklabels(range(1, 32), rotation=90, color='white')
            ax_avg_expenses_per_day.set_yticklabels(ax_avg_expenses_per_day.get_yticks(), color='white')

            # Display the plot
            st.pyplot(fig_avg_expenses_per_day)
    else:
        st.write("No monthly results available. Please upload files in the Home view.")
