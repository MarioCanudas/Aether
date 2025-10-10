import streamlit as st
from models.views_data import PeriodsOptions

def period_select_box(key: str) -> str:
    return st.selectbox(
        label= "Period",
        options= PeriodsOptions.get_values(),
        index= 0,
        placeholder= "Select period to analyze",
        key= key
    )