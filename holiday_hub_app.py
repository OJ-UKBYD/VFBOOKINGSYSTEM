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
DB_FILE = "bookings_v7_db.json"

def load_bookings():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                if not df.empty and "Start Date" in df.columns and "End Date" in df.columns:
                    df["Start Date"] = pd.to_datetime(df["Start Date"]).dt.date
                    df["End Date"] = pd.to_datetime(df["End Date"]).dt.date
                return df
        except:
            pass
            
    # Clean baseline database structure layout matching single property rules
    df_default = pd.DataFrame([
        {
            "Booking ID": "BK-1001", 
            "Guest": "Alice Smith", 
            "Email": "alice@example.com",
            "Start Date": datetime.date(2026, 10, 5), 
            "End Date": datetime.date(2026, 10, 12), 
            "Phone": "+1 555-0199", 
            "Flight Info": "BA173", 
            "Notes": "Prefers early check-in if possible."
        },
        {
            "Booking ID": "BK-1002", 
            "Guest": "Bob Jones", 
            "Email": "bob@example.com",
            "Start Date": datetime.date(2026, 10, 15), 
            "End Date": datetime.date(2026, 10, 20), 
            "Phone": "", 
            "Flight Info": "", 
            "Notes": ""
        }
    ])
    return df_default

def save_bookings(df):
    df_to_save = df.copy()
    if not df_to_save.empty:
        df_to_save["Start Date"] = df_to_save["Start Date"].apply(lambda x: x.isoformat() if isinstance(x, datetime.date) else str(x))
        df_to_save["End Date"] = df_to_save["End Date"].apply(lambda x: x.isoformat() if isinstance(x, datetime.date) else str(x))
    df_to_save.to_json(DB_FILE, orient="records", indent=4)

# --- STATE MANAGEMENT ---
if "bookings" not in st.session_state:
    st.session_state.bookings = load_bookings()

if "logs" not in st.session_state:
    st.session_state.logs = ["System Initialized... Waiting for reservation inputs."]

if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# Ensure all critical optional columns exist safely
required_columns = ["Phone", "Flight Info", "Notes", "Email"]
for col in required_columns:
    if col not in st.session_state.bookings.columns:
        st.session_state.bookings[col] = ""


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏨 Holiday Hub Navigation")
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
            bid = row['Booking ID']
            with st.container():
                
                if st.session_state.editing_id == bid:
                    st.markdown(f"#### 📝 Amend Booking: `{bid}`")
                    with st.form(f"edit_form_{bid}", clear_on_submit=False):
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_name = st.text_input("Primary Guest Full Name:", value=row['Guest'])
                            edit_email = st.text_input("Guest Email Address:", value=row['Email'])
                        with col_e2:
                            edit_in = st.date_input("Check-In Date", value=row['Start Date'])
                            edit_out = st.date_input("Check-Out Date", value=row['End Date'])
                            
                        st.markdown("---")
                        col_e3, col_e4 = st.columns(2)
                        with col_e3:
                            edit_phone = st.text_input("Phone Number:", value=row['Phone'])
                        with col_e4:
                            edit_flight = st.text_input("Flight Details / Number:", value=row['Flight Info'])
                            
                        edit_notes = st.text_area("Reservation Notes or Special Requests:", value=row['Notes'])
                        
                        btn_col1, btn_col2 = st.columns(2)
                        save_btn = btn_col1.form_submit_button("Save Changes", type="primary")
                        cancel_btn = btn_col2.form_submit_button("Cancel")
                        
                        if save_btn:
                            if not edit_name:
                                st.error("Missing Requirement: Please provide a guest name.")
                            elif edit_in >= edit_out:
                                st.error("Error: Check-Out Date must fall cleanly after your chosen Check-In Date.")
                            else:
                                has_overlap = False
                                for _, res in st.session_state.bookings.iterrows():
                                    if res["Booking ID"] != bid:
                                        if (edit_in <= res["End Date"]) and (edit_out >= res["Start Date"]):
                                            has_overlap = True
                                            break
                                
                                if has_overlap:
                                    st.error("❌ Date Conflict: The modified dates overlap an existing reservation stay.")
                                else:
                                    match_idx = st.session_state.bookings[st.session_state.bookings['Booking ID'] == bid].index
                                    st.session_state.bookings.at[match_idx, "Guest"] = edit_name
                                    st.session_state.bookings.at[match_idx, "Email"] = edit_email
                                    st.session_state.bookings.at[match_idx, "Start Date"] = edit_in
                                    st.session_state.bookings.at[match_idx, "End Date"] = edit_out
                                    st.session_state.bookings.at[match_idx, "Phone"] = edit_phone
                                    st.session_state.bookings.at[match_idx, "Flight Info"] = edit_flight
                                    st.session_state.bookings.at[match_idx, "Notes"] = edit_notes
                                    
                                    save_bookings(st.session_state.bookings)
                                    st.session_state.editing_id = None
                                    st.toast("Booking details updated successfully!")
                                    st.rerun()
                                    
                        if cancel_btn:
                            st.session_state.editing_id = None
                            st.rerun()
                else:
                    b_col1, b_col2, b_col3 = st.columns([1.5, 1.5, 1])
                    
                    b_col1.markdown(
                        f"""**ID:** `{bid}` <br> 
                        👤 **Guest:** {row['Guest']} <br> 

