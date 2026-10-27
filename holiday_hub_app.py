
import streamlit as st
import pandas as pd
import datetime
import calendar
import json
import os
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Holiday Hub Booking System",
    page_icon="🏨",
    layout="wide",
)

DB_FILE = "bookings_v3_db.json"
COLUMNS = [
    "Booking ID", "Guest", "Email", "Start Date",
    "End Date", "Phone", "Flight Info", "Notes"
]
TODAY = datetime.date.today()


# --- DATABASE / DATA PERSISTENCE ---
def load_bookings():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            df = pd.DataFrame(data)

            for column in COLUMNS:
                if column not in df.columns:
                    df[column] = ""

            if not df.empty:
                for column in ("Start Date", "End Date"):
                    df[column] = pd.to_datetime(
                        df[column], errors="coerce"
                    ).dt.date

                df["Booking ID"] = df["Booking ID"].astype(str)
                df["Guest"] = df["Guest"].fillna("").astype(str)

                for column in ("Email", "Phone", "Flight Info", "Notes"):
                    df[column] = df[column].fillna("").astype(str)

                df = df[COLUMNS]

            return df

        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            st.warning(
                "The booking data file could not be read. "
                "A fresh sample register has been loaded. "
                "Check the JSON file before saving if it contains "
                "important bookings."
            )

    # Sample bookings for a first run
    return pd.DataFrame([
        {
            "Booking ID": "BK-1001",
            "Guest": "Alice Smith",
            "Email": "alice@example.com",
            "Start Date": datetime.date(2026, 10, 5),
            "End Date": datetime.date(2026, 10, 12),
            "Phone": "+1 555-0199",
            "Flight Info": "BA173",
            "Notes": "Prefers early check-in if possible.",
        },
        {
            "Booking ID": "BK-1002",
            "Guest": "Bob Jones",
            "Email": "bob@example.com",
            "Start Date": datetime.date(2026, 10, 15),
            "End Date": datetime.date(2026, 10, 20),
            "Phone": "",
            "Flight Info": "",
            "Notes": "",
        },
    ], columns=COLUMNS)


def save_bookings(df):
    saved = df.copy()

    for column in ("Start Date", "End Date"):
        saved[column] = saved[column].apply(
            lambda value: value.isoformat()
            if isinstance(
                value,
                (datetime.date, datetime.datetime, pd.Timestamp)
            )
            else str(value)
        )

    saved.to_json(
        DB_FILE,
        orient="records",
        indent=4,
        force_ascii=False
    )


def next_booking_id(df):
    numbers = []

    for booking_id in df.get(
        "Booking ID", pd.Series(dtype=str)
    ).astype(str):
        match = re.fullmatch(r"BK-(\d+)", booking_id.strip())

        if match:
            numbers.append(int(match.group(1)))

    return f"BK-{max(numbers, default=1000) + 1}"


# --- AVAILABILITY CHECKS ---
def has_date_conflict(bookings, check_in, check_out, exclude_id=None):
    """
    Check occupied nights.

    The checkout day is available for another guest to check in.
    When editing, exclude the booking being amended.
    """
    for _, booking in bookings.iterrows():
        if (
            exclude_id is not None
            and str(booking["Booking ID"]) == str(exclude_id)
        ):
            continue

        start = booking["Start Date"]
        end = booking["End Date"]

        if pd.isna(start) or pd.isna(end):
            continue

        if check_in < end and check_out > start:
            return (
                True,
                str(booking["Booking ID"]),
                str(booking["Guest"])
            )

    return False, None, None


def valid_email_or_blank(email):
    email = email.strip()

    return (
        not email
        or bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))
    )


# --- SESSION STATE ---
if "bookings" not in st.session_state:
    st.session_state.bookings = load_bookings()

if "logs" not in st.session_state:
    st.session_state.logs = [
        "System initialised. Waiting for reservation inputs."
    ]

for column in COLUMNS:
    if column not in st.session_state.bookings.columns:
        st.session_state.bookings[column] = ""

st.session_state.bookings = st.session_state.bookings[COLUMNS]


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏨 Holiday Hub Navigation")

page = st.sidebar.radio(
    "Go to:",
    [
        "📊 Dashboard & Calendar",
        "➕ New Booking Request"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "New bookings and amended reservations update "
    "the calendar automatically."
)


# ============================================================
# PAGE 1: DASHBOARD AND CALENDAR
# ============================================================
if page == "📊 Dashboard & Calendar":

    st.title("📊 Property Management Dashboard")
    st.subheader("Property Availability Calendar")

    # --- MONTH AND YEAR SELECTORS ---
    pick_col1, pick_col2 = st.columns([1, 2])

    with pick_col1:
        year_options = list(
            range(TODAY.year - 5, TODAY.year + 11)
        )

        selected_year = st.selectbox(
            "Year",
            options=year_options,
            index=5
        )

    with pick_col2:
        month_names = list(calendar.month_name)[1:]

        selected_month_name = st.selectbox(
            "Month",
            options=month_names,
            index=TODAY.month - 1
        )

    year = int(selected_year)
    month = month_names.index(selected_month_name) + 1

    st.markdown(
        f"#### {calendar.month_name[month]} {year}"
    )

    st.caption(
        "Green = available · Red = booked · "
        "Blue outline = today"
    )

    month_grid = calendar.monthcalendar(year, month)

    days_of_week = [
        "Mon", "Tue", "Wed", "Thu",
        "Fri", "Sat", "Sun"
    ]

    # --- CALENDAR HEADINGS ---
    header_cols = st.columns(7)

    for idx, day_name in enumerate(days_of_week):
        header_cols[idx].markdown(
            f"""
            <div style="
                text-align:center;
                font-weight:700;
                color:#888;
                padding:4px;
            ">
                {day_name}
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- CALENDAR GRID ---
    for week in month_grid:
        week_cols = st.columns(7)

        for idx, day in enumerate(week):

            if day == 0:
                week_cols[idx].markdown(
                    "<div style='min-height:76px'></div>",
                    unsafe_allow_html=True
                )
                continue

            current_date = datetime.date(year, month, day)

            active_bookings = []

            for _, booking in st.session_state.bookings.iterrows():
                start = booking["Start Date"]
                end = booking["End Date"]

                # Checkout date is not an occupied night
                if (
                    pd.notna(start)
                    and pd.notna(end)
                    and start <= current_date < end
                ):
                    active_bookings.append(
                        str(booking["Guest"])
                    )

            is_today = current_date == TODAY
            is_booked = bool(active_bookings)

            bg_color = "#DC3545" if is_booked else "#238636"

            border = (
                "3px solid #1687ff"
                if is_today
                else "1px solid rgba(255,255,255,0.18)"
            )

            status = (
                ", ".join(active_bookings)
                if is_booked
                else "Available"
            )

            today_label = (
                "<span style='font-size:10px;font-weight:700;"
                "display:block;margin-top:2px'>TODAY</span>"
                if is_today
                else ""
            )

            week_cols[idx].markdown(
                f"""
                <div style="
                    background:{bg_color};
                    color:white;
                    padding:8px 4px;
                    border-radius:7px;
                    text-align:center;
                    margin-bottom:8px;
                    min-height:76px;
                    border:{border};
                    box-sizing:border-box;
                ">
                    <span style="
                        font-size:16px;
                        font-weight:700;
                        display:block
                    ">{day}</span>

                    {today_label}

                    f"""<span style="
    font-size:11px;
    font-weight:600;
    display:block;
    white-space:normal;
    overflow-wrap:anywhere;
    margin-top:6px;
">{status}</span>"""
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- BOOKING REGISTER ---
    st.markdown("---")
    st.subheader("📋 Booking Register")

    bookings = st.session_state.bookings

    if bookings.empty:
        st.info("No reservations have been recorded.")

    else:
        for _, row in bookings.sort_values(
            "Start Date", na_position="last"
        ).iterrows():

            booking_id = str(row["Booking ID"])
            guest = str(row["Guest"])

            with st.container(border=True):

                info_col, dates_col, actions_col = st.columns(
                    [1.3, 1.5, 1]
                )

                info_col.markdown(
                    f"**{guest}**  \n"
                    f"Booking ID: `{booking_id}`  \n"
                    f"Email: {row['Email'] or 'Not provided'}"
                )

                info_col.markdown(
                    f"Phone: {row['Phone'] or 'Not provided'}  \n"
                    f"Flight: {row['Flight Info'] or 'Not provided'}"
                )

                dates_col.markdown(
                    f"**Stay**  \n"
                    f"{row['Start Date']} to {row['End Date']}  \n"
                    f"**Notes:** {row['Notes'] or 'None'}"
                )

                # --- EDIT AND CANCEL BUTTONS ---
                with actions_col:

                    if st.button(
                        "Edit booking",
                        key=f"edit_toggle_{booking_id}",
                        use_container_width=True
                    ):
                        edit_key = f"editing_{booking_id}"

                        st.session_state[edit_key] = not (
                            st.session_state.get(edit_key, False)
                        )

                    if st.button(
                        "Cancel booking",
                        key=f"cancel_{booking_id}",
                        type="secondary",
                        use_container_width=True
                    ):
                        st.session_state.bookings = (
                            st.session_state.bookings[
                                st.session_state.bookings[
                                    "Booking ID"
                                ].astype(str) != booking_id
                            ].reset_index(drop=True)
                        )

                        save_bookings(st.session_state.bookings)

                        st.session_state.logs.append(
                            f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] "
                            f"Booking {booking_id} cancelled."
                        )

                        st.toast("Booking cancelled.")
                        st.rerun()

                # --- AMEND BOOKING FORM ---
                if st.session_state.get(
                    f"editing_{booking_id}", False
                ):

                    with st.form(f"edit_form_{booking_id}"):

                        st.markdown(
                            f"**Amend reservation {booking_id}**"
                        )

                        e1, e2 = st.columns(2)

                        with e1:
                            edited_guest = st.text_input(
                                "Guest full name",
                                value=guest,
                                key=f"edit_guest_{booking_id}"
                            )

                            edited_email = st.text_input(
                                "Email (optional)",
                                value=str(row["Email"] or ""),
                                key=f"edit_email_{booking_id}"
                            )

                            edited_phone = st.text_input(
                                "Phone",
                                value=str(row["Phone"] or ""),
                                key=f"edit_phone_{booking_id}"
                            )

                        with e2:
                            edited_start = st.date_input(
                                "Check-in",
                                value=row["Start Date"],
                                key=f"edit_start_{booking_id}"
                            )

                            edited_end = st.date_input(
                                "Check-out",
                                value=row["End Date"],
                                key=f"edit_end_{booking_id}"
                            )

                            edited_flight = st.text_input(
                                "Flight details",
                                value=str(row["Flight Info"] or ""),
                                key=f"edit_flight_{booking_id}"
                            )

                        edited_notes = st.text_area(
                            "Notes / special requests",
                            value=str(row["Notes"] or ""),
                            key=f"edit_notes_{booking_id}"
                        )

                        save_edit = st.form_submit_button(
                            "Save amendments"
                        )

                        if save_edit:

                            if not edited_guest.strip():
                                st.error(
                                    "Please enter a guest name."
                                )

                            elif edited_start >= edited_end:
                                st.error(
                                    "Check-out must be after check-in."
                                )

                            elif not valid_email_or_blank(
                                edited_email
                            ):
                                st.error(
                                    "Enter a valid email address "
                                    "or leave the email field blank."
                                )

                            else:
                                conflict, other_id, other_guest = (
                                    has_date_conflict(
                                        st.session_state.bookings,
                                        edited_start,
                                        edited_end,
                                        exclude_id=booking_id
                                    )
                                )

                                if conflict:
                                    st.error(
                                        f"Those dates overlap booking "
                                        f"{other_id} ({other_guest})."
                                    )

                                else:
                                    mask = (
                                        st.session_state.bookings[
                                            "Booking ID"
                                        ].astype(str) == booking_id
                                    )

                                    st.session_state.bookings.loc[
                                        mask,
                                        [
                                            "Guest", "Email", "Phone",
                                            "Start Date", "End Date",
                                            "Flight Info", "Notes"
                                        ]
                                    ] = [
                                        edited_guest.strip(),
                                        edited_email.strip(),
                                        edited_phone.strip(),
                                        edited_start,
                                        edited_end,
                                        edited_flight.strip(),
                                        edited_notes.strip()
                                    ]

                                    save_bookings(
                                        st.session_state.bookings
                                    )

                                    st.session_state.logs.append(
                                        f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] "
                                        f"Booking {booking_id} amended."
                                    )

                                    st.session_state[
                                        f"editing_{booking_id}"
                                    ] = False

                                    st.toast(
                                        "Booking amendments saved."
                                    )
                                    st.rerun()

    # --- ACTIVITY LOG ---
    if st.session_state.logs:
        st.markdown("---")

        with st.expander("System activity log"):
            for log in reversed(st.session_state.logs):
                st.code(log, language="text")


# ============================================================
# PAGE 2: NEW BOOKING
# ============================================================
elif page == "➕ New Booking Request":

    st.title("➕ Create New Reservation")

    st.markdown(
        "Enter the guest and stay details below. "
        "Email and phone details are optional."
    )

    with st.form("booking_form", clear_on_submit=True):

        st.markdown("#### Guest and stay details")

        form_col1, form_col2 = st.columns(2)

        with form_col1:
            guest_name = st.text_input(
                "Primary guest full name",
                placeholder="John Doe"
            )

            guest_email = st.text_input(
                "Guest email address (optional)",
                placeholder="john.doe@example.com"
            )

            guest_phone = st.text_input(
                "Phone number (optional)",
                placeholder="+44 7700 900000"
            )

        with form_col2:
            check_in = st.date_input(
                "Check-in date",
                value=TODAY,
                key="new_checkin"
            )

            check_out = st.date_input(
                "Check-out date",
                value=TODAY + datetime.timedelta(days=7),
                key="new_checkout"
            )

            flight_info = st.text_input(
                "Flight details / number (optional)",
                placeholder="BA123 or arrival time"
            )

        guest_notes = st.text_area(
            "Reservation notes or special requests (optional)",
            placeholder="Add details here..."
        )

        submit_btn = st.form_submit_button(
            "Create reservation",
            type="primary"
        )

    # --- VALIDATE AND SAVE NEW BOOKING ---
    if submit_btn:

        if not guest_name.strip():
            st.error("Please provide a guest name.")

        elif check_in >= check_out:
            st.error("Check-out must be after check-in.")

        elif not valid_email_or_blank(guest_email):
            st.error(
                "Enter a valid email address or leave "
                "the email field blank."
            )

        else:
            conflict, other_id, other_guest = has_date_conflict(
                st.session_state.bookings,
                check_in,
                check_out
            )

            if conflict:
                st.error(
                    f"Date conflict: these dates overlap "
                    f"booking {other_id} ({other_guest})."
                )

            else:
                new_id = next_booking_id(
                    st.session_state.bookings
                )

                new_record = {
                    "Booking ID": new_id,
                    "Guest": guest_name.strip(),
                    "Email": guest_email.strip(),
                    "Start Date": check_in,
                    "End Date": check_out,
                    "Phone": guest_phone.strip(),
                    "Flight Info": flight_info.strip(),
                    "Notes": guest_notes.strip(),
                }

                st.session_state.bookings = pd.concat(
                    [
                        st.session_state.bookings,
                        pd.DataFrame([new_record])
                    ],
                    ignore_index=True
                )[COLUMNS]

                save_bookings(st.session_state.bookings)

                timestamp = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                if guest_email.strip():
                    log_message = (
                        f"[{timestamp}] Simulated confirmation "
                        f"email recorded for {guest_email.strip()} "
                        f"(booking {new_id})."
                    )
                else:
                    log_message = (
                        f"[{timestamp}] Booking {new_id} created. "
                        "No email supplied, so no confirmation "
                        "email was recorded."
                    )

                st.session_state.logs.append(log_message)

                st.success(
                    f"Reservation {new_id} created successfully."
                )

                if guest_email.strip():
                    st.caption(
                        "This app records a simulated email log. "
                        "It does not send a real email."
                    )

