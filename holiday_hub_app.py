import streamlit as st
import pandas as pd
import datetime
import calendar
import json
import os
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Holiday Hub Booking System",
    page_icon="🏨",
    layout="wide"
)

# --- SELF-HEALING JSON DATABASE PERSISTENCE ---
DB_FILE = "bookings_v6_json.json"

def load_bookings_from_json():
    """Loads text from JSON file with smart data-type recovery and self-healing columns."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
            if data:
                df = pd.DataFrame(data)
                
                # Dynamic Code Adaptation: Map old database names to new names instantly
                if "Flight Info" in df.columns and "Arrival Flight" not in df.columns:
                    df.rename(columns={"Flight Info": "Arrival Flight"}, inplace=True)
                
                # Self-Healing Layer: Guarantee all 7 custom inputs exist safely without breaking
                required_cols = ["Booking ID", "Guest", "Email", "Start Date", "End Date", "Phone", "Arrival Flight", "Return Flight", "Notes"]
                for col in required_cols:
                    if col not in df.columns:
                        df[col] = ""
                
                # Strict Date Typing Parse
                df["Start Date"] = pd.to_datetime(df["Start Date"]).dt.date
                df["End Date"] = pd.to_datetime(df["End Date"]).dt.date
                return df
        except Exception as e:
            # Fallback alert in terminal if parse goes wrong
            print(f"JSON Auto-Healing Log: Structural adjustments handled ({e})")
            
    # Default Mock Entries initialized immediately if no database exists
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
            "Phone": "+44 7700 900077", 
            "Arrival Flight": "FR102", 
            "Return Flight": "FR103",
            "Notes": "Will need cot setup."
        }
    ])
    return df_default

def save_bookings_to_json(df):
    """Converts dates to plain ISO strings safely before saving to the file workspace."""
    df_to_save = df.copy()
    if not df_to_save.empty:
        df_to_save["Start Date"] = df_to_save["Start Date"].apply(lambda x: x.isoformat() if isinstance(x, datetime.date) else str(x))
        df_to_save["End Date"] = df_to_save["End Date"].apply(lambda x: x.isoformat() if isinstance(x, datetime.date) else str(x))
    df_to_save.to_json(DB_FILE, orient="records", indent=4)


# --- STATE LIFECYCLE MANAGEMENT ---
if "bookings" not in st.session_state:
    st.session_state.bookings = load_bookings_from_json()

if "logs" not in st.session_state:
    st.session_state.logs = ["System Initialized with JSON Storage Engine... Standby."]

if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# Protect interactive button scopes from losing state updates on top-down pass redraws
st.session_state.bookings = load_bookings_from_json()


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏨 Holiday Hub Navigation")

if st.session_state.editing_id:
    st.sidebar.warning(f"⚠️ App Locked: Amending {st.session_state.editing_id}")
    page = "📊 Dashboard & Calendar"
else:
    page = st.sidebar.radio("Go to:", ["📊 Dashboard & Calendar", "➕ New Booking Request"])


# --- PAGE 1: DASHBOARD & CALENDAR OVERVIEW ---
if page == "📊 Dashboard & Calendar":
    st.title("📊 Property Management Dashboard")
    st.subheader("Property Availability Calendar Matrix")
    
    col_c1, _ = st.columns([3, 7])
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
    
    # --- DEDICATED INLINE AMENDMENT SUITE ---
    if st.session_state.editing_id:
        target_id = st.session_state.editing_id
        match_df = st.session_state.bookings[st.session_state.bookings["Booking ID"] == target_id]
        
        if not match_df.empty:
            booking_to_edit = match_df.iloc[0] # Fixed row index selection rule
            
            st.info(f"📝 Currently Amending Booking: **{target_id}**")
            
            ec1, ec2 = st.columns(2)
            with ec1:
                edit_name = st.text_input("Guest Full Name:", value=booking_to_edit['Guest'])
                edit_email = st.text_input("Email Address:", value=booking_to_edit['Email'])
                edit_phone = st.text_input("Phone Number:", value=booking_to_edit['Phone'])
            with ec2:
                edit_in = st.date_input("Check-In Date:", value=booking_to_edit['Start Date'])
                edit_out = st.date_input("Check-Out Date:", value=booking_to_edit['End Date'])
                edit_arr = st.text_input("Arrival Flight Code:", value=booking_to_edit['Arrival Flight'])
                edit_ret = st.text_input("Return Flight Code:", value=booking_to_edit['Return Flight'])
                
            edit_notes = st.text_area("Reservation Notes:", value=booking_to_edit['Notes'])
            
            ctrl1, ctrl2, _ = st.columns([1.5, 1.5, 7])
            if ctrl1.button("💾 Save Amendment", type="primary"):
                if not edit_name or not edit_email:
                    st.error("Name and Email parameters are required.")
                elif edit_in >= edit_out:
                    st.error("Check-Out must fall after Check-In Date.")
                else:
                    # Overlap Checker Rules
                    has_overlap = False
                    for _, res in st.session_state.bookings.iterrows():
                        if res["Booking ID"] != target_id:
                            if (edit_in < res["End Date"]) and (edit_out > res["Start Date"]):
                                has_overlap = True
                                break
                    if has_overlap:
                        st.error("❌ Conflict: This change overlaps an existing stay.")
                    else:
                        # Locate original index value and update elements back to memory arrays cleanly
                        idx_match = st.session_state.bookings[st.session_state.bookings["Booking ID"] == target_id].index
                        st.session_state.bookings.at[idx_match[0], "Guest"] = edit_name
                        st.session_state.bookings.at[idx_match[0], "Email"] = edit_email
                        st.session_state.bookings.at[idx_match[0], "Phone"] = edit_phone
                        st.session_state.bookings.at[idx_match[0], "Start Date"] = edit_in
                        st.session_state.bookings.at[idx_match[0], "End Date"] = edit_out
                        st.session_state.bookings.at[idx_match[0], "Arrival Flight"] = edit_arr
                        st.session_state.bookings.at[idx_match[0], "Return Flight"] = edit_ret
                        st.session_state.bookings.at[idx_match[0], "Notes"] = edit_notes
                        
                        save_bookings_to_json(st.session_state.bookings)
                        st.session_state.editing_id = None

