import streamlit as st
import asyncio
from constants.views_icons import PROFILE_ICON
from components import modify_profile_popup
from controllers import ProfileConfigController

def show_profile() -> None:
    """
    Display user profile information with account statistics and activity metrics.
    Shows a clean, organized view of user data including account age, activity stats, and timestamps.
    """
    # Page config
    st.set_page_config(
        page_title='Profile',
        page_icon=PROFILE_ICON,
        layout='centered'
    )

    controller = ProfileConfigController()
    view_data = asyncio.run(controller.get_profile_view_data())

    # Header section
    st.title('👤 Profile')

    # User info card
    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="Username",
                value=view_data.profile.username,
                help="Username of the user"
            )

        with col2:
            # Account age metric
            st.metric(
                label="Account Age",
                value=view_data.account_age_formatted,
                help="Time since account creation"
            )


    # Account statistics section
    st.header('📊 Account Statistics')

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Total Transactions",
                value=f"{view_data.transaction_count:,}",
                help="Total number of transactions recorded"
            )

        with col2:
            st.metric(
                label="Active Goals",
                value=f"{view_data.goal_count:,}",
                help="Total number of goals created"
            )

        with col3:
            # Activity indicator based on days since last transaction
            if view_data.days_since_last_transaction is None:
                # No transactions uploaded yet
                activity_status = "No transactions"
                delta_color = "off"
                delta_value = None
                help_text = "No transactions have been uploaded yet"
            elif view_data.days_since_last_transaction == 0:
                activity_status = "Today"
                delta_color = "normal"
                delta_value = "0 days"
                help_text = "Last transaction was uploaded today"
            elif view_data.days_since_last_transaction == 1:
                activity_status = "Yesterday"
                delta_color = "normal"
                delta_value = "1 day"
                help_text = "Last transaction was uploaded yesterday"
            elif view_data.days_since_last_transaction < 7:
                activity_status = f"{view_data.days_since_last_transaction} days ago"
                delta_color = "normal"
                delta_value = f"{view_data.days_since_last_transaction} days"
                help_text = "Days since last transaction upload"
            elif view_data.days_since_last_transaction < 30:
                activity_status = f"{view_data.days_since_last_transaction} days ago"
                delta_color = "off"
                delta_value = f"{view_data.days_since_last_transaction} days"
                help_text = "Days since last transaction upload"
            else:
                activity_status = f"{view_data.days_since_last_transaction} days ago"
                delta_color = "inverse"
                delta_value = f"{view_data.days_since_last_transaction} days"
                help_text = "Days since last transaction upload"

            st.metric(
                label="Last Activity",
                value=activity_status,
                delta=delta_value,
                delta_color=delta_color,
                help=help_text
            )

    # Account details section
    st.header('📅 Account Details')

    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Account Created**")
            st.write(f"📆 {view_data.profile.created_at_formatted}")

            st.markdown("**Last Login**")
            st.write(f"🔐 {view_data.profile.last_login_formatted}")

        with col2:
            st.markdown("**Profile Updated**")
            if view_data.profile.updated_at:
                st.write(f"✏️ {view_data.profile.updated_at_formatted}")
            else:
                st.write("✏️ Not updated yet")
                st.caption("Profile has not been modified since creation")

    if st.button('Modify Profile', icon= ':material/edit:', type= 'primary', key= 'modify_profile_button'):
        modify_profile_popup(view_data.profile)
