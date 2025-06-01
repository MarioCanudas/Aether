import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def show_income_analysis():
    st.title('Income Analysis')

    # Check if monthly results are available
    if 'all_monthly_results' in st.session_state and not st.session_state.all_monthly_results.empty:
        st.write("Analysis based on monthly results")

        # Convert 'Month' to a string format for plotting
        monthly_results = st.session_state.all_monthly_results.copy()
        monthly_results['Month'] = monthly_results['Month'].astype(str)

        # Bar chart for Total Income
        st.subheader('Total Income by Month')
        fig_income, ax_income = plt.subplots()

        # Plot the data
        ax_income.bar(monthly_results['Month'], monthly_results['total_income'], color='blue')

        # Transparent background, white grid on Y-axis only, and white labels
        fig_income.patch.set_alpha(0)
        ax_income.set_facecolor('none')
        ax_income.grid(True, color='gray', linestyle='-', linewidth=0.5, axis='y')
        ax_income.set_xticklabels(monthly_results['Month'], rotation=90, color='white')
        ax_income.set_yticklabels(ax_income.get_yticks(), color='white')

        st.pyplot(fig_income)

        # Check if processed data is available for daily income analysis
        if 'all_processed_data' in st.session_state and not st.session_state.all_processed_data.empty:
            processed_data = st.session_state.all_processed_data.copy()
            processed_data['Date'] = pd.to_datetime(processed_data['Date'])

            # Filter to include only rows with non-zero income
            income_data = processed_data[processed_data['Income'] > 0]
            income_data['Day'] = income_data['Date'].dt.day

            # Average income by day of the month
            avg_income_per_day = income_data.groupby('Day')['Income'].mean().reindex(range(1, 32), fill_value=0)

            st.subheader('Average Income by Day')
            fig_avg_income_per_day, ax_avg_income_per_day = plt.subplots()
            ax_avg_income_per_day.bar(avg_income_per_day.index, avg_income_per_day, color='green')

            # Transparent background, Y-axis grid only, and white labels
            fig_avg_income_per_day.patch.set_alpha(0)
            ax_avg_income_per_day.set_facecolor('none')
            ax_avg_income_per_day.grid(True, color='gray', linestyle='-', linewidth=0.5, axis='y')
            ax_avg_income_per_day.set_xticks(range(1, 32))
            ax_avg_income_per_day.set_xticklabels(range(1, 32), rotation=90, color='white')
            ax_avg_income_per_day.set_yticklabels(ax_avg_income_per_day.get_yticks(), color='white')

            st.pyplot(fig_avg_income_per_day)
    else:
        st.write("No monthly results available. Please upload files in the Home view.")
