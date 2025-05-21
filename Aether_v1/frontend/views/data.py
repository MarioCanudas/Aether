import streamlit as st

def show_data():
    st.title('Data')

    # Check if data is available in session state
    if 'all_processed_data' in st.session_state and not st.session_state.all_processed_data.empty:
        st.write("Data available in Data View")

        # Display the processed data table or use it for further analysis
        st.dataframe(st.session_state.all_processed_data)
    else:
        st.write("No data available. Please upload files in the Home view.")
