import streamlit as st
from controllers import CategoriesConfigController
from models.categories import CategoryGroup, NewCategory

@st.dialog('New Category')
def new_category_popup():
    with st.form(key= 'new_category_form', border= False, clear_on_submit= True):
        controller = CategoriesConfigController()
        
        new_category_group = st.selectbox(
            'Group', 
            options= CategoryGroup.get_values(), 
            index= None, 
            key= 'new_category_group'
        )
        
        left, right = st.columns([1, 3])
        
        new_category_name = left.text_input('Name', key= 'new_category_name')
        
        new_category_description = right.text_input('Description', key= 'new_category_description')
        
        if st.form_submit_button('Add category', type= 'primary'):
            try:
                new_category = NewCategory(
                    group= CategoryGroup(new_category_group),
                    name= new_category_name,
                    description= new_category_description
                )
            except ValueError as e:
                st.warning(f'Some field is invalid, try again', icon= ':material/warning:')
            
            try:
                controller.add_category(new_category)
                st.toast('Category added successfully', icon= ':material/check:')
                st.rerun()
            except ValueError as e:
                st.warning(f'Category already exists, try again', icon= ':material/warning:')