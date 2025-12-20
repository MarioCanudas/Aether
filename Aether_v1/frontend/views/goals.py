from typing import Any, cast

import streamlit as st
from components import add_amount_popup, config_goals_templates_popup, new_goal_popup
from constants.views_icons import GOALS_ICON
from controllers import GoalsController
from utils import give_amount_format


def show_goals():
    # Page config
    st.set_page_config(page_title="Goals", page_icon=GOALS_ICON, layout="centered")
    controller = GoalsController()

    st.title("Goals")

    left, right, _ = st.columns([1, 1, 3])

    if left.button(
        "Goal",
        icon=":material/add:",
        type="primary",
        help="Add a new goal",
        key="new_goal_button",
        width="stretch",
    ):
        new_goal_popup()

    if right.button(
        "Templates",
        icon=":material/edit:",
        type="secondary",
        key="goals_templates_button",
        help="Add or modify goals templates",
    ):
        config_goals_templates_popup()

    st.header("Info")

    left, right = st.columns([3, 1])

    goal_to_view = left.selectbox(
        "Choose a goal",
        controller.get_current_goals_names(),
        key="view_goals_status",
        label_visibility="collapsed",
        placeholder="Select a goal",
        help="Select a goal to view its information",
    )

    goal_info = controller.get_goal_info(goal_to_view) if goal_to_view else None

    if right.button("Modify", type="primary", key="modify_goal_button", disabled=not goal_to_view):
        if goal_info:
            add_amount_popup(goal_info.goal_id)

    if goal_info:
        left, right = st.columns(2)

        left.write(
            f"""
            **Type:** {goal_info.type.value} \n
            **Category:** {goal_info.category}
            """
        )

        right.write(
            f"""
            **Period:** {goal_info.start_date} - {goal_info.end_date} \n
            """
        )
        cast(Any, right).badge(
            goal_info.status.value, icon=goal_info.status.icon, color=goal_info.status.color
        )

        left, center, right = st.columns(3)

        left.metric("Goal", give_amount_format(goal_info.amount + goal_info.added_amount))
        center.metric("Remaining", give_amount_format(goal_info.remaining))
        right.metric(
            goal_info.custom_current_amount_name,
            give_amount_format(goal_info.current_amount),
            delta=f"{int(goal_info.progress_porcentage * 100)}%",
            delta_color="normal" if goal_info.progress_porcentage < 1 else "inverse",
        )

        progress_donut_chart = controller.get_donut_chart_goal_progress(goal_info)

        st.subheader(
            "Progress", help="The graph shows the progress of the goal in fuction of the amounts."
        )
        st.pyplot(progress_donut_chart)

        progress_line_chart = controller.get_line_chart_goal_progress(goal_info)
        st.altair_chart(progress_line_chart, width="stretch")

        progress_score = controller.get_goal_progress_score(goal_info)
        st.markdown(
            f"<h2 style='text-align: center;'>{progress_score.label} progress</h2>",
            unsafe_allow_html=True,
        )

    else:
        st.info("No goal selected")

    with st.expander("Current Goals"):
        df = controller.get_current_goals()

        if df.empty:
            st.write("No current goals")
        else:
            st.dataframe(df, hide_index=True, width="stretch")

    with st.expander("Past Goals"):
        df = controller.get_past_goals()

        if df.empty:
            st.write("No past goals")
        else:
            st.dataframe(df, hide_index=True, width="stretch")
