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
DB_FILE = "bookings_v5.db"

def init_db():
    """Initializes the SQLite database and ensures the schema is locked down."""
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
    
    # Check if database is empty to inject clean fallback entries if needed
    cursor.execute("SELECT COUNT(*) FROM bookings")
    if cursor.fetchone() == 0:
        seed_data = [
            ("BK-1001", "Alice Smith", "alice@example.com", "2026-10-05", "2026-10-12", "+1 555-0199", "BA173", "BA174", "Prefers early check-in if possible."),
            ("BK-1002", "Bob Jones", "bob@example.com", "2026-10-15", "2026-10-20", "", "", "", "")
        ]
        cursor.executemany('''
            INSERT INTO bookings (booking_id, guest_name, email, start_date, end_date, phone, arrival_flight, return_flight, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', seed_data)
        conn.commit()
    conn.close()

def load_bookings_from_db():
    """Reads transactional data rows back out into a standard Pandas DataFrame."""
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
    """Inserts a single checked reservation row into the database storage cleanly."""
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
    """Executes a selective SQL UPDATE target on a specific modified index key."""
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
    """Drops the specific record row instantly from persistent storage arrays."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
    conn.commit()
    conn.close()

# --- INITIALIZE DATABASE ARCHITECTURE ---
init_db()

# --- STATE LIFECYCLE MANAGEMENT ---
if "bookings" not in st.session_state:
    st.session_state.bookings = load_bookings_from_db()

if "logs" not in st.session_state:
    st.session_state.logs = ["System Initialized with SQLite Engine Core... Connected ready."]

if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# Always grab the freshest master state data row sequence on refresh passes
st.session_state.bookings = load_bookings_from_db()


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏨 Holiday Hub Navigation")
page = st.sidebar.radio("Go to:", ["📊 Dashboard & Calendar", "➕ New Booking Request"])
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** SQLite architecture ensures your data persists even if you make live code adjustments.")


# --- PAGE 1: DASHBOARD & CALENDAR OVERVIEW ---
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
    
    # --- MODULAR AMENDMENT SUITE WORKSPACE ---
    if st.session_state.editing_id:
        # Pull active targeted booking metadata out cleanly
        target_id = st.session_state.editing_id
        match_df = st.session_state.bookings[st.session_state.bookings["Booking ID"] == target_id]
        
        if not match_df.empty:
            booking_to_edit = match_df.iloc[0]
            st.warning(f"📝 Currently Amending Booking: {target_id}")
            
            # Form-free editor box to bypass layout traps
            with st.container():
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
                
                ctrl1, ctrl2, _ = st.columns([1, 1, 4])
                if ctrl1.button("💾 Save Amendment", type="primary"):
                    if not edit_name or not edit_email:
                        st.error("Name and Email parameters are strictly required.")
                    elif edit_in >= edit_out:
                        st.error("Check-Out must fall cleanly after Check-In.")
                    else:
                        # Overlap verification check matching against other entries
                        has_overlap = False
                        for _, res in st.session_state.bookings.iterrows():
                            if res["Booking ID"] != target_id:
                                if (edit_in < res["End Date"]) and (edit_out > res["Start Date"]):
                                    has_overlap = True
