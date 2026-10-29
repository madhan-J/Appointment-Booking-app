"""
Admin panel component for management and analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import BOOKING_STATUSES, ADMIN_PASSWORD_DEFAULT
from zapier import send_zapier_webhook

def render_admin_panel(repo, webhook_url: str):
    st.header("🔑 Admin Dashboard & Analytics")

    stored_pass = st.secrets.get("ADMIN_PASSWORD", ADMIN_PASSWORD_DEFAULT)
    pwd = st.sidebar.text_input("Admin Password", type="password")

    if pwd != stored_pass:
        st.warning("Enter valid admin password in sidebar to access controls.")
        return

    st.success("Authenticated as Administrator")
    tab1, tab2, tab3 = st.tabs(["📊 Analytics", "📅 Schedule & Bookings", "⚙️ Providers"])

    df_bookings = repo.get_bookings()
    df_providers = repo.get_providers()

    with tab1:
        st.subheader("Performance Metrics")
        if df_bookings.empty:
            st.info("No booking data available yet.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Bookings", len(df_bookings))
            completed = len(df_bookings[df_bookings["status"] == "Completed"])
            cancelled = len(df_bookings[df_bookings["status"] == "Cancelled"])
            no_shows = len(df_bookings[df_bookings["status"] == "No-show"])

            c2.metric("Completed Visits", completed)
            c3.metric("Cancellation Rate", f"{(cancelled / len(df_bookings)) * 100:.1f}%")
            c4.metric("No-Show Rate", f"{(no_shows / len(df_bookings)) * 100:.1f}%")

            col_a, col_b = st.columns(2)
            with col_a:
                fig1 = px.pie(df_bookings, names="discipline", title="Bookings by Discipline")
                st.plotly_chart(fig1, use_container_width=True)
            with col_b:
                fig2 = px.histogram(df_bookings, x="start_time", title="Peak Booking Hours", color="discipline")
                st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Booking Management")
        if not df_bookings.empty:
            st.dataframe(df_bookings)
            st.write("---")
            b_id = st.selectbox("Select Booking ID", df_bookings["booking_id"].tolist())
            new_status = st.selectbox("New Status", BOOKING_STATUSES)

            if st.button("Update Status"):
                if repo.update_booking(b_id, {"status": new_status}):
                    st.success(f"Updated {b_id} to {new_status}")
                    st.cache_data.clear()
                    if new_status == "Completed":
                        send_zapier_webhook(webhook_url, {"event": "visit_completed", "booking_id": b_id})
                    elif new_status == "No-show":
                        send_zapier_webhook(webhook_url, {"event": "no_show", "booking_id": b_id})
                    st.rerun()

    with tab3:
        st.subheader("Provider Roster")
        st.dataframe(df_providers)
