import streamlit as st
import asyncio
from utils import give_amount_format
from constants.views_icons import CARDS_ICON
from controllers import CardsViewController
from components import new_card_popup

def show_cards():
    # Page config
    st.set_page_config(
        page_title='Cards',
        page_icon=CARDS_ICON,
        layout='centered'
    )
    controller = CardsViewController()
    
    st.title('Cards')
    
    if st.button('Add Card', icon= ':material/add:', type= 'primary', key= 'add_card_button'):
        new_card_popup()
        
    card_to_view = st.selectbox('Choose a card', controller.get_cards(only_name= True))
    
    if card_to_view:
        card = controller.get_card_by_name(card_to_view)
        view_data = asyncio.run(controller.get_card_view_data(card.card_id))
        
        left1, center1, right1 = st.columns(3)
        
        with left1:
            st.metric(label= 'Total income', value= give_amount_format(view_data.metrics.total_income))
            
        with center1:
            st.metric(label= 'Total expenses', value= give_amount_format(view_data.metrics.total_expenses))
            
        with right1:
            st.metric(label= 'Total balance', value= give_amount_format(view_data.metrics.total_balance))
        
        left2, right2 = st.columns([3, 1.5])
        
        with left2:
            st.altair_chart(view_data.income_vs_expenses_chart) if view_data.income_vs_expenses_chart else st.info('No data available', icon= ':material/info:')
            
        with right2:
            st.dataframe(view_data.get_last_transactions(in_df= True), hide_index= True)
            
    else:
        st.info('Select a card to view', icon= ':material/info:')