import streamlit as st
import pandas as pd
import datetime
import calendar
import sqlite3
import os
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Holiday Hub Booking System",
    page_icon="🏨",
    layout="wide"
)

# --- DATABASE / RELATIONAL DATA PERSISTENCE ---
DB_FILE = "bookings_v6.db"

def init_db():
    """Initializes the SQLite database with all 7 user-requested input fields."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            guest_name TEXT NOT NULL,
            email TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            phone TEXT,
            arrival_flight TEXT,
            return_flight TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    
    # Inject Mock/Seed Bookings immediately if the database is brand new
    cursor.execute("SELECT COUNT(*) FROM bookings")
    if cursor.fetchone() == 0:
        seed_data = [
            ("BK-1001", "Alice Smith", "alice@example.com", "2026-10-05", "2026-10-12", "+1 555-0199", "BA173", "BA174", "Prefers early check-in if possible."),
            ("BK-1002", "Bob Jones", "bob@example.com", "2026-10-15", "2026-10-20", "+44 7700 900077", "FR102", "FR103", "Will need cot setup.")
        ]
        cursor.executemany('''
            INSERT INTO bookings (booking_id, guest_name, email, start_date, end_date, phone, arrival_flight, return_flight, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', seed_data)
        conn.commit()
    conn.close()

def load_bookings_from_db():
    """Reads SQLite rows securely back into a clean Pandas DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()
    
    if not df.empty:
        df.rename(columns={
            "booking_id": "Booking ID",
            "guest_name": "Guest",
            "email": "Email",
            "start_date": "Start Date",
            "end_date": "End Date",
            "phone": "Phone",
            "arrival_flight": "Arrival Flight",
            "return_flight": "Return Flight",
            "notes": "Notes"
        }, inplace=True)
        df["Start Date"] = pd.to_datetime(df["Start Date"]).dt.date
        df["End Date"] = pd.to_datetime(df["End Date"]).dt.date
    else:
        df = pd.DataFrame(columns=["Booking ID", "Guest", "Email", "Start Date", "End Date", "Phone", "Arrival Flight", "Return Flight", "Notes"])
    return df

def add_booking_to_db(record):
    """Inserts a new guest reservation record."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bookings (booking_id, guest_name, email, start_date, end_date, phone, arrival_flight, return_flight, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record["Booking ID"], record["Guest"], record["Email"],
        record["Start Date"].isoformat(), record["End Date"].isoformat(),
        record["Phone"], record["Arrival Flight"], record["Return Flight"], record["Notes"]
    ))
    conn.commit()
    conn.close()

def update_booking_in_db(record):
    """Updates an existing guest record using its unique Booking ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE bookings 
        SET guest_name = ?, email = ?, start_date = ?, end_date = ?, phone = ?, arrival_flight = ?, return_flight = ?, notes = ?
        WHERE booking_id = ?
    ''', (
        record["Guest"], record["Email"], record["Start Date"].isoformat(), record["End Date"].isoformat(),
        record["Phone"], record["Arrival Flight"], record["Return Flight"], record["Notes"], record["Booking ID"]
    ))
    conn.commit()
    conn.close()

def delete_booking_from_db(booking_id):
    """Permanently purges a record from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
    conn.commit()
    conn.close()

# --- INITIALIZE DATABASE ---
init_db()

# --- STATE MANAGEMENT ---
if "logs" not in st.session_state:
    st.session_state.logs = ["System Initialized with SQLite Engine... Ready."]

if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# Fresh data pull on every application redraw pass
st.session_state.bookings = load_bookings_from_db()


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏨 Holiday Hub Navigation")

# If an edit is active, lock navigation focus to help you save updates safely
if st.session_state.editing_id:
    st.sidebar.warning(f"⚠️ Locked: Amending {st.session_state.editing_id}")
    page = "📊 Dashboard & Calendar"
else:
    page = st.sidebar.radio("Go to:", ["📊 Dashboard & Calendar", "➕ New Booking Request"])


# --- PAGE 1: DASHBOARD & CALENDAR ---
if page == "📊 Dashboard & Calendar":
    st.title("📊 Property Management Dashboard")
    st.subheader("Property Availability Calendar Matrix")
    
    col_c1, _ = st.columns([2, 5])
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
    
    # --- FIXED AMENDMENT WORKSPACE SUITE ---
    if st.session_state.editing_id:
        target_id = st.session_state.editing_id
        match_df = st.session_state.bookings[st.session_state.bookings["Booking ID"] == target_id]
        
        if not match_df.empty:
            # Fixed index access bug [0] to stop silent crashing
            booking_to_edit = match_df.iloc[0]
            
            st.info(f"📝 Currently Amending Booking: **{target_id}**")
            
            # Form-free dynamic editing panels
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
                    # Overlap Validation (ignores itself)
                    has_overlap = False
                    for _, res in st.session_state.bookings.iterrows():
                        if res["Booking ID"] != target_id:
                            if (edit_in < res["End Date"]) and (edit_out > res["Start Date"]):
                                has_overlap = True
                                break
                    if has_overlap:
                        st.error("❌ Conflict: This change overlaps an existing stay.")
                    else:
                        updated_record = {
                            "Booking ID": target_id,
