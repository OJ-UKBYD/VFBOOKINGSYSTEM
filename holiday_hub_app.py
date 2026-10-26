import streamlit as st
import pandas as pd
import datetime
import calendar
import json
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Holiday Hub Booking System",
    page_icon="🏨",
    layout="wide"
)

# --- DATABASE / DATA PERSISTENCE ---
# Google Sheets is used as the persistent backend.
#
# Streamlit secrets required:
#
# [gcp_service_account]
# type = "service_account"
# project_id = "your-project-id"
# private_key_id = "..."
# private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
# client_email = "..."
# client_id = "..."
# auth_uri = "https://accounts.google.com/o/oauth2/auth"
# token_uri = "https://oauth2.googleapis.com/token"
# auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
# client_x509_cert_url = "..."
#
# [google_sheets]
# spreadsheet_id = "YOUR_GOOGLE_SHEET_ID"
# worksheet_name = "Bookings"
#
# Install dependencies:
#   pip install gspread google-auth

import gspread
from google.oauth2.service_account import Credentials

SHEET_COLUMNS = [
    "Booking ID",
    "Guest",
    "Email",
    "Start Date",
    "End Date",
    "Phone",
    "Flight Info",
    "Notes",
]

@st.cache_resource
def get_google_sheet():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError(
            "Google Sheets is not configured. Add [gcp_service_account] "
            "to Streamlit secrets."
        )

    spreadsheet_id = st.secrets.get("google_sheets", {}).get("spreadsheet_id")
    worksheet_name = st.secrets.get("google_sheets", {}).get(
        "worksheet_name", "Bookings"
    )

    if not spreadsheet_id:
        raise RuntimeError(
            "Missing google_sheets.spreadsheet_id in Streamlit secrets."
        )

    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=len(SHEET_COLUMNS),
        )
        worksheet.append_row(SHEET_COLUMNS)

    return worksheet


def load_bookings():
    worksheet = get_google_sheet()
    records = worksheet.get_all_records()

    if not records:
        worksheet.update("A1:H1", [SHEET_COLUMNS])
        return pd.DataFrame(columns=SHEET_COLUMNS)

    df = pd.DataFrame(records)

    for col in SHEET_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[SHEET_COLUMNS]

    if not df.empty:
        df["Start Date"] = pd.to_datetime(
            df["Start Date"], errors="coerce"
        ).dt.date
        df["End Date"] = pd.to_datetime(
            df["End Date"], errors="coerce"
        ).dt.date

    return df


def save_bookings(df):
    worksheet = get_google_sheet()

    df_to_save = df.copy()

    for col in SHEET_COLUMNS:
        if col not in df_to_save.columns:
            df_to_save[col] = ""

    df_to_save = df_to_save[SHEET_COLUMNS]

    for col in ["Start Date", "End Date"]:
        df_to_save[col] = df_to_save[col].apply(
            lambda x: x.isoformat()
            if isinstance(x, (datetime.date, datetime.datetime))
            else ("" if pd.isna(x) else str(x))
        )

    df_to_save = df_to_save.fillna("")
    values = [SHEET_COLUMNS] + df_to_save.astype(str).values.tolist()

    # Replace the sheet contents in one operation.
    worksheet.clear()
    worksheet.update(
        range_name=f"A1:H{len(values)}",
        values=values,
    )


# --- STATE MANAGEMENT ---
if "bookings" not in st.session_state:
    try:
        st.session_state.bookings = load_bookings()
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        st.stop()

if "logs" not in st.session_state:
    st.session_state.logs = ["System Initialized... Waiting for reservation inputs."]


if "editing_booking_id" not in st.session_state:
    st.session_state.editing_booking_id = None

# Ensure all critical optional columns exist safely
required_columns = ["Phone", "Flight Info", "Notes", "Email"]
for col in required_columns:
    if col not in st.session_state.bookings.columns:
        st.session_state.bookings[col] = ""


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏨 Holiday Hub Navigation")
st.sidebar.caption("☁️ Booking data is stored in Google Sheets")
page = st.sidebar.radio("Go to:", ["📊 Dashboard & Calendar", "➕ New Booking Request"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** New bookings instantly update the calendar grid block view on the dashboard page.")


# --- PAGE 1: DASHBOARD & CALENDAR ---
if page == "📊 Dashboard & Calendar":
    st.title("📊 Property Management Dashboard")
    st.subheader("Property Availability Calendar Matrix")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        calendar_start = st.date_input("Calendar Start View", datetime.date(2026, 10, 1))
    
    year = calendar_start.year
    month = calendar_start.month
    
    st.write(f"##### Grid view for {calendar.month_name[month]} {year}")
    
    cal = calendar.monthcalendar(year, month)
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    header_cols = st.columns(7)
    for idx, day_name in enumerate(days_of_week):
        header_cols[idx].markdown(f"<p style='text-align:center; font-weight:bold; color:#888; margin-bottom:2px;'>{day_name}</p>", unsafe_allow_html=True)
        
    for week in cal:
        week_cols = st.columns(7)
        for idx, day in enumerate(week):
            if day == 0:
                week_cols[idx].write("")
            else:
                current_date = datetime.date(year, month, day)
                
                is_booked = False
                guest_label = ""
                for _, row in st.session_state.bookings.iterrows():
                    if row["Start Date"] <= current_date <= row["End Date"]:
                        is_booked = True
                        guest_label = row["Guest"]
                        break
                        
                bg_color = "#DC3545" if is_booked else "#28A745"
                status_text = f"Booked: {guest_label}" if is_booked else "Available"
                
                week_cols[idx].markdown(
                    f'''<div style="
                        background-color: {bg_color}; 
                        color: white; 
                        padding: 10px; 
                        border-radius: 6px; 
                        text-align: center; 
                        margin-bottom: 8px;
                        min-height: 65px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    ">
                        <span style="font-size: 14px; font-weight: bold; display: block;">{day}</span>
                        <span style="font-size: 9px; opacity: 0.95; display: block;">{status_text}</span>
                    </div>''', 
                    unsafe_allow_html=True
                )

    st.markdown("---")
    st.subheader("📋 Active Master Booking Registers")
    
    if st.session_state.bookings.empty:
        st.info("No active reservations detected.")
    else:
        for idx, row in st.session_state.bookings.iterrows():
            with st.container():
                b_col1, b_col2, b_col3 = st.columns([1.5, 1.5, 1])
                
                b_col1.markdown(
                    f"""**ID:** `{row['Booking ID']}` <br> 
                    👤 **Guest:** {row['Guest']} <br> 
                    ✉️ **Email:** {row['Email']}""", 
                    unsafe_allow_html=True
                )
                
                phone_str = row['Phone'] if row['Phone'] else "None"
                flight_str = row['Flight Info'] if row['Flight Info'] else "None"
                notes_str = row['Notes'] if row['Notes'] else "None"
                
                b_col2.markdown(
                    f"""📅 **Timeline:** {row['Start Date']} to {row['End Date']} <br>
                    📞 **Phone:** {phone_str} | ✈️ **Flight:** {flight_str} <br>
                    📝 **Notes:** <em>{notes_str}</em>""", 
                    unsafe_allow_html=True
                )
                
                with b_col3:
                    st.write("")
                    edit_col, cancel_col = st.columns(2)

                    with edit_col:
                        if st.button("✏️ Edit", key=f"edit_{row['Booking ID']}"):
                            st.session_state.editing_booking_id = row["Booking ID"]
                            st.rerun()

                    with cancel_col:
                        if st.button("Cancel", key=f"del_{row['Booking ID']}", type="primary"):
                            st.session_state.bookings = st.session_state.bookings[
                                st.session_state.bookings["Booking ID"] != row["Booking ID"]
                            ]
                            save_bookings(st.session_state.bookings)
                            if st.session_state.editing_booking_id == row["Booking ID"]:
                                st.session_state.editing_booking_id = None
                            st.toast("Booking removed successfully!")
                            st.rerun()

                if st.session_state.editing_booking_id == row["Booking ID"]:
                    booking_id = row["Booking ID"]
                    st.markdown(f"### ✏️ Edit Booking `{booking_id}`")

                    with st.form(f"edit_form_{booking_id}"):
                        edit_col1, edit_col2 = st.columns(2)

                        with edit_col1:
                            edit_guest = st.text_input(
                                "Primary Guest Full Name:",
                                value=str(row["Guest"]),
                                key=f"edit_guest_{booking_id}"
                            )
                            edit_email = st.text_input(
                                "Guest Email Address (optional):",
                                value=str(row["Email"] or ""),
                                placeholder="Leave blank if not required",
                                key=f"edit_email_{booking_id}"
                            )

                        with edit_col2:
                            edit_check_in = st.date_input(
                                "Check-In Date",
                                value=row["Start Date"],
                                key=f"edit_check_in_{booking_id}"
                            )
                            edit_check_out = st.date_input(
                                "Check-Out Date",
                                value=row["End Date"],
                                key=f"edit_check_out_{booking_id}"
                            )

                        edit_col3, edit_col4 = st.columns(2)

                        with edit_col3:
                            edit_phone = st.text_input(
                                "Phone Number:",
                                value=str(row["Phone"] or ""),
                                key=f"edit_phone_{booking_id}"
                            )

                        with edit_col4:
                            edit_flight = st.text_input(
                                "Flight Details / Number:",
                                value=str(row["Flight Info"] or ""),
                                key=f"edit_flight_{booking_id}"
                            )

                        edit_notes = st.text_area(
                            "Reservation Notes or Special Requests:",
                            value=str(row["Notes"] or ""),
                            key=f"edit_notes_{booking_id}"
                        )

                        save_edit = st.form_submit_button("💾 Save Changes", type="primary")
                        close_edit = st.form_submit_button("Close Without Saving")

                    if close_edit:
                        st.session_state.editing_booking_id = None
                        st.rerun()

                    if save_edit:
                        if not edit_guest.strip():
                            st.error("Missing Requirement: Please provide a guest name.")
                        elif edit_check_in >= edit_check_out:
                            st.error("Error: Check-Out Date must fall cleanly after your chosen Check-In Date.")
                        elif booking_has_overlap(
                            edit_check_in,
                            edit_check_out,
                            exclude_booking_id=booking_id
                        ):
                            st.error("❌ Date Conflict: the property is already reserved during those selected dates.")
                        else:
                            booking_index = st.session_state.bookings[
                                st.session_state.bookings["Booking ID"] == booking_id
                            ].index

                            if len(booking_index) == 1:
                                idx = booking_index[0]
                                st.session_state.bookings.at[idx, "Guest"] = edit_guest.strip()
                                st.session_state.bookings.at[idx, "Email"] = edit_email.strip()
                                st.session_state.bookings.at[idx, "Start Date"] = edit_check_in
                                st.session_state.bookings.at[idx, "End Date"] = edit_check_out
                                st.session_state.bookings.at[idx, "Phone"] = edit_phone.strip()
                                st.session_state.bookings.at[idx, "Flight Info"] = edit_flight.strip()
                                st.session_state.bookings.at[idx, "Notes"] = edit_notes.strip()

                                save_bookings(st.session_state.bookings)
                                log_booking_action(
                                    "UPDATED",
                                    booking_id,
                                    edit_guest.strip(),
                                    edit_email.strip(),
                                    edit_check_in,
                                    edit_check_out,
                                    edit_phone.strip(),
                                    edit_flight.strip(),
                                    edit_notes.strip()
                                )

                                st.session_state.editing_booking_id = None
                                st.success(f"Booking {booking_id} updated successfully.")
                                st.rerun()

                st.markdown("<hr style='margin:10px 0; border:0.5px solid #333;'>", unsafe_allow_html=True)

        if st.session_state.logs:
            st.markdown("---")
            with st.expander("✉️ System Confirmation Outbox Logs (Simulated)"):
                for log in reversed(st.session_state.logs):
                    st.code(log, language="text")


# --- PAGE 2: NEW BOOKING REQUEST ---
elif page == "➕ New Booking Request":
    st.title("➕ Create New Lodging Reservation")
    st.markdown("Fill out the criteria details below to allocate schedule availability.")
    
    with st.form("booking_form", clear_on_submit=True):
        st.markdown("#### 🔑 Essential Criteria")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            guest_name = st.text_input("Primary Guest Full Name:", placeholder="John Doe")
            guest_email = st.text_input(
                "Guest Email Address (optional):",
                placeholder="Leave blank if not required"
            )
        with col_f2:
            check_in = st.date_input("Check-In Date", datetime.date(2026, 10, 5))
            check_out = st.date_input("Check-Out Date", datetime.date(2026, 10, 12))
            
        st.markdown("---")
        st.markdown("#### 📋 Optional Information")
        col_f3, col_f4 = st.columns(2)
        with col_f3:
            guest_phone = st.text_input("Phone Number:", placeholder="+1 (555) 000-0000")
        with col_f4:
            flight_info = st.text_input("Flight Details / Number:", placeholder="AA123 or Arrival Time")
            
        guest_notes = st.text_area("Reservation Notes or Special Requests:", placeholder="Add details here...")
        
        submit_btn = st.form_submit_button("Verify & Dispatch Booking")
        
        if submit_btn:
            if not guest_name:
                st.error("Missing Requirement: Please provide a guest name.")
            elif check_in >= check_out:
                st.error("Error: Check-Out Date must fall cleanly after your chosen Check-In Date.")
            else:
                has_overlap = False
                for _, res in st.session_state.bookings.iterrows():
                    if (check_in <= res["End Date"]) and (check_out >= res["Start Date"]):
                        has_overlap = True
                        break
                
                if has_overlap:
                    st.error("❌ Date Conflict: The property is already reserved during those selected dates.")
                else:
                    new_id = get_next_booking_id()
                    new_record = {
                        "Booking ID": new_id,
                        "Guest": guest_name,
                        "Email": guest_email,
                        "Start Date": check_in,
                        "End Date": check_out,
                        "Phone": guest_phone,
                        "Flight Info": flight_info,
                        "Notes": guest_notes
                    }
                    
                    st.session_state.bookings = pd.concat([st.session_state.bookings, pd.DataFrame([new_record])], ignore_index=True)
                    save_bookings(st.session_state.bookings)
                    
                    log_booking_action(
                        "CREATED",
                        new_id,
                        guest_name.strip(),
                        guest_email.strip(),
                        check_in,
                        check_out,
                        guest_phone.strip(),
                        flight_info.strip(),
                        guest_notes.strip()
                    )

                    email_message = (
                        f"Confirmation simulated for {guest_email.strip()}."
                        if guest_email.strip()
                        else "Booking saved without an email address."
                    )
                    
                    st.markdown(
                        f'''<div style="background-color: #28A745; color: white; padding: 15px; border-radius: 6px; margin-bottom:15px;">
                        <strong>🎉 Reservation Success!</strong> Booking <code>{new_id}</code> registered successfully.
                        {email_message}<br>
                        </div>''', 
                        unsafe_allow_html=True
                    )
