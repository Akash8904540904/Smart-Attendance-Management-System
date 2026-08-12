import os
import numpy as np
import pandas as pd
import streamlit as st

# File paths
STUDENTS_FILE = "students.csv"
ATTENDANCE_FILE = "attendance_records.csv"


def load_data():
    # Load or initialize students dataset
    if os.path.exists(STUDENTS_FILE):
        students_df = pd.read_csv(STUDENTS_FILE)
    else:
        students_df = pd.DataFrame(
            columns=["Roll No", "Name", "Department", "Semester"]
        )
        students_df.to_csv(STUDENTS_FILE, index=False)

    # Load or initialize attendance dataset
    if os.path.exists(ATTENDANCE_FILE):
        attendance_df = pd.read_csv(ATTENDANCE_FILE)
    else:
        attendance_df = pd.DataFrame(columns=["Date", "Roll No", "Status"])
        attendance_df.to_csv(ATTENDANCE_FILE, index=False)

    return students_df, attendance_df


def save_students(df):
    df.to_csv(STUDENTS_FILE, index=False)


def save_attendance(df):
    df.to_csv(ATTENDANCE_FILE, index=False)


st.set_page_config(page_title="Smart Attendance Management System", layout="wide")
st.title("📋 Smart Attendance Management System")

students_df, attendance_df = load_data()

# Navigation Sidebar
module = st.sidebar.radio(
    "Select Module",
    [
        "Student Registration",
        "Attendance Entry",
        "Attendance Calculation",
        "Data Analysis",
        "Report Generation",
    ],
)

# ---------------------------------------------------------
# Module 1: Student Registration
# ---------------------------------------------------------
if module == "Student Registration":
    st.header("👤 Student Registration")

    with st.form("register_student_form"):
        roll_no = st.text_input("Roll Number")
        name = st.text_input("Student Name")
        department = st.selectbox(
            "Department",
            ["Computer Science", "Information Technology", "Electronics", "Mechanical"],
        )
        semester = st.number_input("Semester", min_value=1, max_value=8, step=1)
        submit = st.form_submit_button("Register Student")

        if submit:
            if not roll_no.strip() or not name.strip():
                st.error("Roll Number and Name are required!")
            elif roll_no in students_df["Roll No"].astype(str).values:
                st.error("Roll Number already registered!")
            else:
                new_student = {
                    "Roll No": roll_no.strip(),
                    "Name": name.strip(),
                    "Department": department,
                    "Semester": semester,
                }
                students_df = pd.concat(
                    [students_df, pd.DataFrame([new_student])], ignore_index=True
                )
                save_students(students_df)
                st.success(f"Student '{name}' registered successfully!")

    st.subheader("Registered Students List")
    st.dataframe(students_df, use_container_width=True)

# ---------------------------------------------------------
# Module 2: Attendance Entry
# ---------------------------------------------------------
elif module == "Attendance Entry":
    st.header("📝 Daily Attendance Entry")

    if students_df.empty:
        st.warning("No students registered yet. Please register students first.")
    else:
        selected_date = st.date_input("Select Date")
        formatted_date = selected_date.strftime("%Y-%m-%d")

        # Check if attendance already recorded for this date
        existing_records = attendance_df[attendance_df["Date"] == formatted_date]
        if not existing_records.empty:
            st.info(f"Attendance for {formatted_date} has already been logged.")

        with st.form("attendance_entry_form"):
            st.subheader(f"Mark Attendance for {formatted_date}")
            attendance_status = {}

            for idx, row in students_df.iterrows():
                r_no = str(row["Roll No"])
                s_name = row["Name"]
                # Default status selection
                attendance_status[r_no] = st.radio(
                    f"{s_name} (Roll No: {r_no})",
                    ["Present", "Absent"],
                    horizontal=True,
                    key=f"att_{r_no}",
                )

            save_entry = st.form_submit_button("Submit Attendance")

            if save_entry:
                # Remove existing records for this date if updating
                attendance_df = attendance_df[attendance_df["Date"] != formatted_date]

                new_entries = []
                for r_no, status in attendance_status.items():
                    new_entries.append(
                        {"Date": formatted_date, "Roll No": r_no, "Status": status}
                    )

                attendance_df = pd.concat(
                    [attendance_df, pd.DataFrame(new_entries)], ignore_index=True
                )
                save_attendance(attendance_df)
                st.success(f"Attendance recorded for {formatted_date}!")

# ---------------------------------------------------------
# Module 3: Attendance Calculation
# ---------------------------------------------------------
elif module == "Attendance Calculation":
    st.header("🧮 Attendance Calculation")

    if students_df.empty or attendance_df.empty:
        st.warning("Insufficient data to calculate attendance statistics.")
    else:
        # Calculate summary statistics using Pandas & NumPy
        total_days = len(attendance_df["Date"].unique())

        merged_df = pd.merge(students_df, attendance_df, on="Roll No", how="left")

        # NumPy conditional calculation for numerical conversion
        merged_df["Present_Numeric"] = np.where(
            merged_df["Status"] == "Present", 1, 0
        )

        summary = (
            merged_df.groupby(["Roll No", "Name", "Department"])
            .agg(
                Total_Classes=("Date", "nunique"),
                Attended_Classes=("Present_Numeric", "sum"),
            )
            .reset_index()
        )

        # NumPy calculation for attendance percentage
        summary["Attendance %"] = np.round(
            np.where(
                summary["Total_Classes"] > 0,
                (summary["Attended_Classes"] / summary["Total_Classes"]) * 100,
                0,
            ),
            2,
        )

        st.dataframe(summary, use_container_width=True)

        st.metric("Total Academic Sessions Recorded", total_days)

# ---------------------------------------------------------
# Module 4: Data Analysis Module
# ---------------------------------------------------------
elif module == "Data Analysis":
    st.header("📊 Attendance Data Analysis")

    if students_df.empty or attendance_df.empty:
        st.warning("Insufficient data available for visual analysis.")
    else:
        merged_df = pd.merge(students_df, attendance_df, on="Roll No", how="left")
        merged_df["Present_Numeric"] = np.where(
            merged_df["Status"] == "Present", 1, 0
        )

        calc_df = (
            merged_df.groupby(["Roll No", "Name", "Department"])
            .agg(
                Total=("Date", "nunique"), Attended=("Present_Numeric", "sum")
            )
            .reset_index()
        )

        calc_df["Attendance %"] = np.round(
            (calc_df["Attended"] / calc_df["Total"]) * 100, 2
        )

        # Threshold slider for low-attendance warning
        threshold = st.slider(
            "Low Attendance Threshold (%)",
            min_value=50,
            max_value=90,
            value=75,
        )

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🚩 Students Below Threshold")
            low_attendance_df = calc_df[calc_df["Attendance %"] < threshold]
            if low_attendance_df.empty:
                st.success(
                    f"No students currently below {threshold}% attendance threshold!"
                )
            else:
                st.dataframe(
                    low_attendance_df[
                        ["Roll No", "Name", "Department", "Attendance %"]
                    ],
                    use_container_width=True,
                )

        with col2:
            st.subheader("📈 Average Attendance by Department")
            dept_avg = (
                calc_df.groupby("Department")["Attendance %"].mean().reset_index()
            )
            st.bar_chart(data=dept_avg, x="Department", y="Attendance %")

# ---------------------------------------------------------
# Module 5: Report Generation
# ---------------------------------------------------------
elif module == "Report Generation":
    st.header("📥 Report Generation & Export")

    if students_df.empty or attendance_df.empty:
        st.warning("No data available to generate reports.")
    else:
        merged_df = pd.merge(students_df, attendance_df, on="Roll No", how="left")
        merged_df["Present_Numeric"] = np.where(
            merged_df["Status"] == "Present", 1, 0
        )

        report_df = (
            merged_df.groupby(["Roll No", "Name", "Department", "Semester"])
            .agg(
                Total_Classes=("Date", "nunique"),
                Attended_Classes=("Present_Numeric", "sum"),
            )
            .reset_index()
        )

        report_df["Attendance_Percentage"] = np.round(
            (report_df["Attended_Classes"] / report_df["Total_Classes"]) * 100, 2
        )

        st.subheader("Overall Master Summary")
        st.dataframe(report_df, use_container_width=True)

        # CSV Export Option
        csv_data = report_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Download Master Attendance Report (CSV)",
            data=csv_data,
            file_name="Attendance_Master_Report.csv",
            mime="text/csv",
        )
