import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional

import pandas as pd
import streamlit as st
import uuid


import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "status_app.db")
BIWEEKLY_ANCHOR_THURSDAY = date(2026, 4, 2)


# ---------- Database ----------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def seed_user(cur, username: str, password: str, full_name: str, role: str):
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing = cur.fetchone()

    if existing is None:
        cur.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            (username, password, full_name, role),
        )
    else:
        cur.execute(
            "UPDATE users SET password = ?, full_name = ?, role = ? WHERE username = ?",
            (password, full_name, role, username),
        )


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('manager', 'employee'))
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            period_label TEXT NOT NULL,
            accomplishments TEXT,
            submitted_at TEXT NOT NULL,
            UNIQUE(user_id, period_label),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
       """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            update_id INTEGER NOT NULL,
            task_name TEXT,
            description TEXT,
            blockers TEXT,
            overall_status TEXT,
            FOREIGN KEY(update_id) REFERENCES updates(id)
        )
        """
    )

    conn.commit()

    # Demo users
    # Manager
    cur.execute("DELETE FROM users WHERE username = ?", ("manager",))
    seed_user(cur, "j.stebbins@gotion.com", "Temp@123", "Jason Stebbins", "manager")
# Employees with temporary password
    employees = [
        ("p.uppari@gotion.com", "Praveen Kumar Uppari"),
        ("v.pathuri@gotion.com", "Venkata Pichaiah Pathuri"),
        ("v.taduru@gotion.com", "Vinay Kumar Taduru"),
        ("d.faulkner@gotion.com", "Duane Faulkner"),
        ("l.wadley@gotion.com", "Lucas Wadley"),
        ("a.ghanem@gotion.com", "Ahmad Ghanem"),
        ("g.yan@gotion.com", "Chris Yan"),
        ("l.wang10@gotion.com", "Jupiter (Liuzixin) Wang"),
    ]

    for username, full_name in employees:
        seed_user(cur, username, "Temp@123", full_name, "employee")

    conn.commit()
    conn.close()


# ---------- Helpers ----------
def current_biweekly_period(input_date: Optional[date] = None) -> str:
    if input_date is None:
        input_date = date.today()

    if input_date <= BIWEEKLY_ANCHOR_THURSDAY:
        meeting_date = BIWEEKLY_ANCHOR_THURSDAY
    else:
        delta_days = (input_date - BIWEEKLY_ANCHOR_THURSDAY).days
        period_number = delta_days // 14
        meeting_date = BIWEEKLY_ANCHOR_THURSDAY + timedelta(days=period_number * 14)

    return f"BW Ending {meeting_date.strftime('%B %d, %Y (%a)')}"


def authenticate(username: str, password: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username.strip(), password.strip()),
    )
    user = cur.fetchone()
    conn.close()
    return user


def get_user_update(user_id: int, period_label: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM updates WHERE user_id = ? AND period_label = ?",
        (user_id, period_label),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_tasks_for_update(update_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM tasks WHERE update_id = ? ORDER BY id",
        (update_id,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows
def delete_update(user_id: int, period_label: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM updates WHERE user_id = ? AND period_label = ?",
        (user_id, period_label),
    )
    row = cur.fetchone()

    if row:
        update_id = row["id"]
        cur.execute("DELETE FROM tasks WHERE update_id = ?", (update_id,))
        cur.execute("DELETE FROM updates WHERE id = ?", (update_id,))
        conn.commit()

    conn.close()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM updates WHERE user_id = ? AND period_label = ?",
        (user_id, period_label),
    )
    row = cur.fetchone()

    if row:
        update_id = row["id"]
        cur.execute("DELETE FROM tasks WHERE update_id = ?", (update_id,))
        cur.execute("DELETE FROM updates WHERE id = ?", (update_id,))
        conn.commit()

    conn.close()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM tasks WHERE update_id = ? ORDER BY id",
        (update_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
def update_password(user_id: int, new_password: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (new_password, user_id),
    )

    conn.commit()
    conn.close()


# EXISTING CODE (do not touch)
def save_update_with_tasks(user_id: int, period_label: str, accomplishments: str, tasks: list[dict]):
    conn = get_connection()
    cur = conn.cursor()

def save_update_with_tasks(user_id: int, period_label: str, accomplishments: str, tasks: list[dict]):
    conn = get_connection()
    cur = conn.cursor()
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """
        INSERT INTO updates (user_id, period_label, accomplishments, submitted_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, period_label)
        DO UPDATE SET
            accomplishments = excluded.accomplishments,
            submitted_at = excluded.submitted_at
        """,
        (user_id, period_label, accomplishments, submitted_at),
    )

    cur.execute(
        "SELECT id FROM updates WHERE user_id = ? AND period_label = ?",
        (user_id, period_label),
    )
    update_row = cur.fetchone()
    update_id = update_row["id"]

    cur.execute("DELETE FROM tasks WHERE update_id = ?", (update_id,))

    for task in tasks:
        cur.execute(
            """
            INSERT INTO tasks (update_id, task_name, description, blockers, overall_status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
               update_id,
               task.get("task_name", ""),
               task.get("description", ""),
               task.get("blockers", ""),
               task.get("overall_status", ""),
            ),
        )

    conn.commit()
    conn.close()


def get_available_periods():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT DISTINCT period_label FROM updates ORDER BY period_label DESC",
        conn,
    )
    conn.close()

    saved_periods = df["period_label"].dropna().tolist()

    today = date.today()
    delta_days = (today - BIWEEKLY_ANCHOR_THURSDAY).days

    if delta_days >= 0:
        current_period_number = delta_days // 14
    else:
        current_period_number = -((-delta_days + 13) // 14)

    generated_periods = []
    for i in range(current_period_number - 6, current_period_number + 7):
        meeting_date = BIWEEKLY_ANCHOR_THURSDAY + timedelta(days=i * 14)
        generated_periods.append(f"BW Ending {meeting_date.strftime('%B %d, %Y (%a)')}")

    all_periods = sorted(set(saved_periods + generated_periods), reverse=True)
    return all_periods


def get_manager_view(period_label: Optional[str] = None):
    conn = get_connection()

    query = """
        SELECT
            u.id as user_id,
            u.full_name,
            u.username,
            up.id as update_id,
            up.period_label,
            up.accomplishments,
            up.submitted_at
        FROM users u
        LEFT JOIN updates up ON u.id = up.user_id
        WHERE u.role = 'employee'
    """
    params = []

    if period_label:
        query += " AND (up.period_label = ? OR up.period_label IS NULL)"
        params.append(period_label)

    query += " ORDER BY u.full_name"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# ---------- Session ----------
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None


def logout():
    st.session_state.logged_in = False
    st.session_state.user = None


# ---------- UI ----------
def login_page():
    col1, col2 = st.columns([1, 4])

    with col1:
        st.image("logo.png", width=200)

    with col2:
        st.title("Biweekly IT Status Tracker")
        st.caption("Employees submit updates. Managers can see the whole team's status.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

    if login_btn:
        user = authenticate(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = dict(user)
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    
        

def employee_dashboard(user):
    st.subheader("My Biweekly Status Update")
    st.caption("Update your accomplishments and task-level progress.")

    selected_period = current_biweekly_period()
    st.markdown(f"### 📅 {selected_period}")

    existing = get_user_update(user["id"], selected_period)
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if existing:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("👁️ View Submitted Data"):
                st.session_state.edit_mode = False

        with col2:
            if st.button("✏️ Edit / Resubmit"):
                st.session_state.edit_mode = True

        with col3:
            if st.button("🗑️ Delete Submission"):
                delete_update(user["id"], selected_period)
                st.session_state.edit_mode = False
                st.success("Submission deleted successfully.")
                st.rerun()
    if existing and not st.session_state.edit_mode:
        st.subheader("📄 Your Submitted Data")

        st.markdown(f"**Accomplishments:** {existing['accomplishments']}")

        tasks = get_tasks_for_update(existing["id"])

        for t in tasks:
            st.markdown(f"""
            **Task:** {t['task_name']}  
            **Description:** {t['description']}  
            **Blockers:** {t['blockers']}  
            **Status:** {t['overall_status']}
            """)

        return  # stops form from showing
    if existing:
       st.success("You have already submitted for this biweekly period. You can edit and resubmit your update below.")
       st.info(f"Last submitted: {existing['submitted_at']}")
    else:
        st.info("No submission yet for this biweekly period.")
    
    existing_tasks = []
    if existing:
        existing_tasks = get_tasks_for_update(existing["id"])

    if "task_items" not in st.session_state:
        st.session_state.task_items = []

    if "loaded_period" not in st.session_state:
        st.session_state.loaded_period = None

    if "remove_task_request" not in st.session_state:
        st.session_state.remove_task_request = None

    # Load tasks only when the selected period changes
    if st.session_state.loaded_period != selected_period:
        if existing_tasks:
            st.session_state.task_items = [
                {
                    "id": str(uuid.uuid4()),
                    "task_name": t["task_name"] or "",
                    "description": t["description"] or "",
                    "blockers": t["blockers"] or "",
                    "overall_status": t["overall_status"] or "In Progress",
                }
                for t in existing_tasks
            ]
        else:
           st.session_state.task_items = [
               {
                   "id": str(uuid.uuid4()),
                   "task_name": "",
                   "description": "",
                   "blockers": "",
                   "overall_status": "In Progress",
                }
]
        st.session_state.loaded_period = selected_period

    # Remove the exact clicked task BEFORE drawing the form
   

    if st.button("➕ Add Task"):
        st.session_state.task_items.append(
            {
                "id": str(uuid.uuid4()),
                "task_name": "",
                "description": "",
                "blockers": "",
                "overall_status": "In Progress",
            }
    )
        st.rerun()

    with st.form("employee_form", clear_on_submit=False):
        accomplishments = st.text_area(
            "Accomplishments / Wins",
            value=existing["accomplishments"] if existing else "",
            height=120,
            placeholder="What did you complete during this period?",
        )

        overall_status_options = ["Completed", "In Progress", "Blocked"]
        tasks_data = []
        remove_task_id = None

        for i, task in enumerate(st.session_state.task_items):
            task_id = task["id"]
            col_task, col_remove = st.columns([8, 1])

            task_title = task["task_name"].strip() if task["task_name"].strip() else f"Task {i + 1}"

            with col_task:
                st.markdown(f"### {task_title}")

            with col_remove:
                if len(st.session_state.task_items) > 1:
                    if st.form_submit_button(
                        f"❌ Remove {task_title}",
                        use_container_width=True,
                    ):
                        remove_task_id = task_id

            task_name = st.text_input(
                f"Task Name {i + 1}",
                value=task["task_name"],
                key=f"task_name_{task_id}",
                placeholder="Enter task name",
            )

            description = st.text_area(
                f"Description {i + 1}",
                value=task["description"],
                height=80,
                key=f"description_{i}",
                placeholder="Enter description for this task",
            )

            blockers = st.text_area(
                f"Blockers {i + 1}",
                value=task["blockers"],
                height=80,
                key=f"blockers_{task_id}",
                placeholder="Any blockers for this task?",
            )

            default_status = (
                task["overall_status"]
                if task["overall_status"] in overall_status_options
                else "In Progress"
            )

            overall_status = st.selectbox(
                f"Overall Status {i + 1}",
                overall_status_options,
                index=overall_status_options.index(default_status),
                key=f"overall_status_{task_id}",
            )

            tasks_data.append(
                {
                    "id": task_id,
                    "task_name": task_name,
                    "description": description,
                    "blockers": blockers,
                    "overall_status": overall_status,
                }
            )

            st.markdown("---")

        submitted = st.form_submit_button("Submit / Resubmit Update")

    # Store the exact clicked task index, then rerun
    if remove_task_id is not None:
        st.session_state.task_items = tasks_data.copy()
        st.session_state.task_items = [
            t for t in st.session_state.task_items
            if t["id"] != remove_task_id
        ]
        st.rerun()

    if submitted:
        valid_tasks = [t for t in tasks_data if t["task_name"].strip()]

        if not accomplishments.strip():
            st.warning("Please enter accomplishments before submitting.")
        elif not valid_tasks:
            st.warning("Please add at least one task with a task name.")
        else:
            st.session_state.task_items = tasks_data

            save_update_with_tasks(
                user["id"],
                selected_period,
                accomplishments,
                valid_tasks,
            )
            st.success(f"Update submitted successfully for {selected_period}")
            st.rerun()

    if existing:
        st.info(f"Last submitted: {existing['submitted_at']}")

def manager_dashboard(user):
    st.subheader("Team Biweekly Status Dashboard")
    st.caption("Review employee submissions for the selected biweekly period.")

    periods = get_available_periods()
    selected_period = st.selectbox("Select Biweekly Period", periods, index=0)

    df = get_manager_view(selected_period)

    total_employees = len(df)
    submitted_count = df["submitted_at"].notna().sum()
    pending_count = total_employees - submitted_count

    col1, col2, col3 = st.columns(3)
    col1.metric("Employees", total_employees)
    col2.metric("Submitted", int(submitted_count))
    col3.metric("Pending", int(pending_count))

    st.subheader("Team Overview")

    if df.empty:
        st.warning("No employee data found.")
        return

    display_df = df.copy()
    display_df["submitted_at"] = display_df["submitted_at"].fillna("Not submitted")
    display_df["period_label"] = display_df["period_label"].fillna(selected_period)
    display_df["accomplishments"] = display_df["accomplishments"].fillna("")

    st.dataframe(display_df, use_container_width=True)

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        data=csv,
        file_name=f"team_status_{selected_period}.csv",
        mime="text/csv",
    )

    st.subheader("Detailed Updates")
    for _, row in display_df.iterrows():
        with st.expander(f"{row['full_name']} ({row['username']})"):
            st.markdown(f"**Period:** {row['period_label']}")
            st.markdown(f"**Submitted:** {row['submitted_at']}")
            st.markdown("**Accomplishments**")
            st.write(row["accomplishments"] or "No update")

            if pd.notna(row["update_id"]):
                tasks = get_tasks_for_update(int(row["update_id"]))
                if tasks:
                    st.markdown("**Tasks**")
                    for idx, task in enumerate(tasks, start=1):
                        st.markdown(f"**Task {idx}: {task['task_name']}**")
                        st.write(f"Description: {task['description'] or 'No update'}")
                        st.write(f"Blockers: {task['blockers'] or 'No blockers'}")
                        st.write(f"Overall Status: {task['overall_status']}")
                        st.markdown("---")
                else:
                    st.write("No tasks submitted.")
            else:
                st.write("No tasks submitted.")


def main():
    st.set_page_config(page_title="Biweekly IT Status Tracker", layout="wide")

    # Hide Streamlit sidebar completely
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
            [data-testid="collapsedControl"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

    init_db()
    init_session()

    if not st.session_state.logged_in:
        login_page()
        return

    user = st.session_state.user

    # Header
    col1, col2 = st.columns([8, 2])

    with col1:
        st.markdown("""
            <div style="
                font-size:26px;
                font-weight:bold;
                padding:10px;
                background-color:#f5f7fa;
                border-radius:10px;
                border:1px solid #ddd;
            ">
                Biweekly IT Status Tracker
            </div>
        """, unsafe_allow_html=True)

    with col2:
        display_role = "IT Director" if user["role"] == "manager" else "Employee"

        with st.popover(f"👤 {user['full_name']} ({display_role})"):
            st.write(f"**Name:** {user['full_name']}")
            st.write(f"**Role:** {display_role}")

            st.markdown("---")
            st.markdown("**🔐 Change Password**")

            current_pwd = st.text_input("Current Password", type="password", key="profile_current_pwd")
            new_pwd = st.text_input("New Password", type="password", key="profile_new_pwd")
            confirm_pwd = st.text_input("Confirm New Password", type="password", key="profile_confirm_pwd")

            if st.button("Update Password", key="profile_update_pwd"):
                if current_pwd != user["password"]:
                    st.error("Current password is incorrect")
                elif new_pwd != confirm_pwd:
                    st.error("New passwords do not match")
                elif len(new_pwd.strip()) < 4:
                    st.error("Password must be at least 4 characters")
                else:
                    update_password(user["id"], new_pwd.strip())
                    st.success("Password updated successfully. Please log in again.")
                    logout()
                    st.rerun()

            st.markdown("---")

            if st.button("Logout", key="header_logout"):
                logout()
                st.rerun()

    st.markdown("---")

    
    # Dashboard
    if user["role"] == "manager":
        manager_dashboard(user)
    else:
        employee_dashboard(user)


if __name__ == "__main__":
    main()
