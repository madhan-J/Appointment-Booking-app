"""
Main Streamlit application entry point.
"""

import uuid
from datetime import datetime
import streamlit as st

from config import DISCIPLINES, NOTIFICATION_CHANNELS, STATUS_CONFIRMED
from storage import get_repository
from slots import get_available_slots, calculate_end_time
from geo import find_nearest_locations, geocode_address, get_google_maps_url
from zapier import send_zapier_webhook
from agent import BookingChatAgent
from admin import render_admin_panel

st.set_page_config(page_title="Appointment Agent", page_icon="📅", layout="wide")

repo = get_repository(st.secrets)
WEBHOOK_URL = st.secrets.get("ZAPIER_WEBHOOK_URL", "")

def main():
    st.title("📅 Multi-Discipline Appointment Booking Agent")

    tabs = st.tabs(["📝 Book Appointment", "🔍 Manage Booking", "💬 Chat Assistant", "🔒 Admin Dashboard"])

    with tabs[0]:
        st.subheader("Step 1: Choose Discipline & Find Location")
        chosen_disc = st.selectbox("Select Discipline", list(DISCIPLINES.keys()))
        disc_info = DISCIPLINES[chosen_disc]
        st.info(f"{disc_info['icon']} {disc_info['description']}")

        user_address = st.text_input("Enter City, Zip Code, or Address:")
        locs = repo.get_locations(discipline=chosen_disc).to_dict("records")

        if user_address:
            coords = geocode_address(user_address)
            if coords:
                sorted_locs = find_nearest_locations(coords[0], coords[1], locs)
                cols = st.columns(min(len(sorted_locs), 3))
                for idx, loc in enumerate(sorted_locs[:3]):
                    with cols[idx]:
                        st.markdown(f"#### {loc['name']}")
                        st.write(f"📍 **{loc['distance_km']} km away**")
                        st.markdown(f"[🗺️ Directions]({get_google_maps_url(loc['lat'], loc['lng'])})")

        if not locs:
            st.error("No locations available.")
            return

        loc_options = {l['name']: l['location_id'] for l in locs}
        selected_loc_name = st.selectbox("Choose branch:", list(loc_options.keys()))
        selected_loc_id = loc_options[selected_loc_name]

        st.write("---")
        st.subheader("Step 2: Service & Availability")

        services = repo.get_services(discipline=chosen_disc).to_dict("records")
        providers = repo.get_providers(location_id=selected_loc_id).to_dict("records")

        if not services or not providers:
            st.error("No services/providers available.")
            return

        serv_map = {s['name']: s for s in services}
        chosen_serv = serv_map[st.selectbox("Service", list(serv_map.keys()))]

        prov_map = {p['name']: p for p in providers}
        chosen_prov = prov_map[st.selectbox("Provider", list(prov_map.keys()))]

        booking_date = st.date_input("Date", min_value=datetime.now().date())

        bookings_df = repo.get_bookings(location_id=selected_loc_id)
        existing_bookings = bookings_df.to_dict("records") if not bookings_df.empty else []

        free_slots = get_available_slots(chosen_prov, int(chosen_serv['duration_min']), str(booking_date), existing_bookings)

        if not free_slots:
            st.warning("No available slots.")
            return

        chosen_slot = st.select_slider("Select Time Slot", options=free_slots)

        st.write("---")
        with st.form("booking_form"):
            c_name = st.text_input("Full Name*")
            c_phone = st.text_input("Phone Number*")
            c_email = st.text_input("Email Address*")
            c_channel = st.selectbox("Preferred Reminder Channel", NOTIFICATION_CHANNELS)

            extra_payload = {}
            for field in disc_info["extra_fields"]:
                if field["type"] == "text":
                    extra_payload[field["name"]] = st.text_input(field['label'])
                elif field["type"] == "textarea":
                    extra_payload[field["name"]] = st.text_area(field['label'])
                elif field["type"] == "number":
                    extra_payload[field["name"]] = st.number_input(field['label'], min_value=1)
                elif field["type"] == "checkbox":
                    extra_payload[field["name"]] = st.checkbox(field['label'])

            if st.form_submit_button("Confirm Booking"):
                if not c_name or not c_phone or not c_email:
                    st.error("Fill required fields.")
                    return

                booking_id = str(uuid.uuid4())[:8]
                end_time = calculate_end_time(chosen_slot, int(chosen_serv['duration_min']))

                booking_obj = {
                    "booking_id": booking_id, "discipline": chosen_disc, "location_id": selected_loc_id,
                    "provider_id": chosen_prov["provider_id"], "service_id": chosen_serv["service_id"],
                    "customer_name": c_name, "phone": c_phone, "email": c_email,
                    "date": str(booking_date), "start_time": chosen_slot, "end_time": end_time,
                    "status": STATUS_CONFIRMED, "channel_pref": c_channel, "extra_fields": extra_payload,
                }

                if repo.add_booking(booking_obj):
                    st.balloons()
                    st.success(f"Booked! Booking ID: **{booking_id}**")
                    send_zapier_webhook(WEBHOOK_URL, {"event": "booking_created", "booking_id": booking_id, **booking_obj})

    with tabs[1]:
        st.subheader("Lookup Appointment")
        search_query = st.text_input("Enter Booking ID or Phone Number:")
        if search_query:
            b_item = repo.get_booking_by_id(search_query)
            b_list = [b_item] if b_item else repo.get_bookings_by_phone(search_query)
            if not b_list:
                st.error("No appointment found.")
            else:
                for b in b_list:
                    st.write(f"**#{b['booking_id']}** - {b['discipline']} ({b['date']} {b['start_time']}) - Status: {b['status']}")

    with tabs[2]:
        st.subheader("🤖 Conversational Assistant")
        agent = BookingChatAgent(st.secrets.get("ANTHROPIC_API_KEY"))
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = [{"role": "assistant", "content": "How can I help you book today?"}]

        for msg in st.session_state["chat_history"]:
            st.chat_message(msg["role"]).write(msg["content"])

        user_input = st.chat_input("Type request...")
        if user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            st.chat_message("user").write(user_input)
            parsed = agent.parse_user_intent(user_input)
            response = f"I understood: Intent `{parsed['intent']}`, Discipline `{parsed['discipline']}`."
            st.session_state["chat_history"].append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)

    with tabs[3]:
        render_admin_panel(repo, WEBHOOK_URL)

if __name__ == "__main__":
    main()
