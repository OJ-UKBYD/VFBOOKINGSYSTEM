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
DB_FILE = "bookings_v4_db.json"

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
            
    df_default = pd.DataFrame([
        {
            "Booking ID": "BK-1001", 
            "Guest": "Alice Smith", 
            "Email": "alice@example.com",
            "Start Date": datetime.date(2026, 10, 5), 
            "End Date": datetime.date(2026, 10, 12), 
            "Phone": "+1 555-0199", 
            "Arrival Flight": "BA173", 
            "Return Flight": "BA174",
            "Notes": "Prefers early check-in if possible."
        },
        {
            "Booking ID": "BK-1002", 
            "Guest": "Bob Jones", 
            "Email": "bob@example.com",
            "Start Date": datetime.date(2026, 10, 15), 
            "End Date": datetime.date(2026, 10, 20), 
            "Phone": "", 
            "Arrival Flight": "", 
            "Return Flight": "",
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

# Maintain edit modes dynamically per booking row
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

required_columns = ["Phone", "Arrival Flight", "Return Flight", "Notes", "Email"]
for col in required_columns:
    if col not in st.session_state.bookings.columns:
        if col == "Arrival Flight" and "Flight Info" in st.session_state.bookings.columns:
            st.session_state.bookings.rename(columns={"Flight Info": "Arrival Flight"}, inplace=True)
        else:
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
                    if row["Start Date"] <= current_date < row["End Date"]:
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
            with st.expander(f"👤 Booking ID: {bid} — Guest: {row['Guest']} ({row['Start Date']} to {row['End Date']})"):
                
                # Check if this booking row has active edit mode toggled on
                if st.session_state.editing_id == bid:
                    st.markdown("#### 📝 Edit Booking Information")
                    with st.form(f"edit_form_{bid}", clear_on_submit=False):
                        e_c1, e_c2 = st.columns(2)
                        with e_c1:
                            edit_name = st.text_input("Guest Name:", value=row['Guest'])
                            edit_email = st.text_input("Email:", value=row['Email'])
                            edit_phone = st.text_input("Phone:", value=row['Phone'])
                        with e_c2:
                            edit_in = st.date_input("Check-In Date:", value=row['Start Date'])
                            edit_out = st.date_input("Check-Out Date:", value=row['End Date'])
                            edit_arr = st.text_input("Arrival Flight:", value=row['Arrival Flight'])
                            edit_ret = st.text_input("Return Flight:", value=row['Return Flight'])
                            
                        edit_notes = st.text_area("Notes:", value=row['Notes'])
                        
                        f_col1, f_col2 = st.columns([1, 6])
                        with f_col1:
                            save_btn = st.form_submit_button("Save changes", type="primary")
                        with f_col2:
                            cancel_edit = st.form_submit_button("Cancel")
                            
                        if save_btn:
                            if not edit_name or not edit_email:
                                st.error("Name and Email parameters are required.")
                            elif edit_in >= edit_out:
                                st.error("Check-Out must fall after Check-In.")
                            else:
                                # Overlap validation matching against other bookings excluding itself
                                has_overlap = False
                                for _, res in st.session_state.bookings.iterrows():
                                    if res["Booking ID"] != bid:
                                        if (edit_in < res["End Date"]) and (edit_out > res["Start Date"]):
                                            has_overlap = True
                                            break
                                            
                                if has_overlap:
                                    st.error("❌ Date Conflict: Changes overlap another reservation window.")
                                else:
                                    # Locate index and assign values back to target entry
                                    match_idx = st.session_state.bookings[st.session_state.bookings['Booking ID'] == bid].index[0]
                                    st.session_state.bookings.at[match_idx, "Guest"] = edit_name
                                    st.session_state.bookings.at[match_idx, "Email"] = edit_email
                                    st.session_state.bookings.at[match_idx, "Phone"] = edit_phone
                                    st.session_state.bookings.at[match_idx, "Start Date"] = edit_in
                                    st.session_state.bookings.at[match_idx, "End Date"] = edit_out
                                    st.session_state.bookings.at[match_idx, "Arrival Flight"] = edit_arr
                                    st.session_state.bookings.at[match_idx, "Return Flight"] = edit_ret
                                    st.session_state.bookings.at[match_idx, "Notes"] = edit_notes
                                    
                                    save_bookings(st.session_state.bookings)
                                    st.session_state.editing_id = None

