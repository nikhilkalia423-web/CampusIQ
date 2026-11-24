import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mysql.connector
from mysql.connector import Error
from database_setup import init_db, get_db_connection, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# Page Config
st.set_page_config(
    page_title="CampusIQ — Relational Student Analytics Portal",
    page_icon="🎓",
    layout="wide"
)

# Sidebar MySQL Connection Settings
st.sidebar.header("🐬 MySQL Database Settings")
st.sidebar.caption("Enter your local MySQL Server credentials below:")
db_host = st.sidebar.text_input("MySQL Host", value=DB_HOST)
db_port = st.sidebar.number_input("MySQL Port", value=DB_PORT, step=1)
db_user = st.sidebar.text_input("MySQL User", value=DB_USER)
db_password = st.sidebar.text_input("MySQL Password", value=DB_PASSWORD, type="password")
db_name = st.sidebar.text_input("Database Name", value=DB_NAME)

def run_query(query, params=None):
    conn = get_db_connection(db_host, int(db_port), db_user, db_password, db_name)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame(rows)

# Header & Project Info
st.title("🎓 CampusIQ — Relational Student Analytics Portal")
st.markdown(
    "**Tech Stack:** MySQL 8.0 (`PRIMARY KEY` & `CHECK` Constraints), Python (`mysql-connector-python`, `Pandas`, `Matplotlib`), `Streamlit`  \n"
    "**Developer:** Nikhil Kalia "
)
st.divider()

# Verify & Initialize MySQL Connection
try:
    init_db(db_host, int(db_port), db_user, db_password, db_name)
    st.sidebar.success(f"✅ Connected to MySQL (`{db_name}`)")
except Error as err:
    st.sidebar.error(f"❌ MySQL Connection Failed")
    st.error(
        f"### 🛑 Unable to Connect to MySQL Server\n"
        f"**Error Details:** `{err}`\n\n"
        f"**How to Fix:**\n"
        f"1. Make sure your MySQL Server is running on `{db_host}:{db_port}`.\n"
        f"2. Enter your MySQL `root` password in the **left sidebar** (`🐬 MySQL Database Settings`) or update `DB_PASSWORD` in `database_setup.py`."
    )
    st.stop()

# Load Data from MySQL
df = run_query("SELECT * FROM students ORDER BY rno ASC")
df["avg"] = df["avg"].astype(float)

anomalies_df = run_query("""
    SELECT * FROM students
    WHERE avg > 35.0
      AND (eng < 35 OR math < 35 OR sci < 35 OR com < 35 OR gk < 35)
    ORDER BY avg DESC
""")
if not anomalies_df.empty:
    anomalies_df["avg"] = anomalies_df["avg"].astype(float)

# Top-level KPI Metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Students", len(df))
col2.metric("Class Average", f"{df['avg'].mean():.2f}%")
col3.metric("Highest Average", f"{df['avg'].max():.2f}%", df.loc[df['avg'].idxmax(), 'name'])
col4.metric("At-Risk Anomalies (Avg>35, Subj<35)", len(anomalies_df), delta="Action Required", delta_color="inverse")
col5.metric("Overall Fail (Avg <= 35)", len(df[df['avg'] <= 35]))

st.divider()

# Multi-Tab Navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Leaderboards & Overview",
    "🚨 Automated Anomaly Detection",
    "📊 Interactive Matplotlib Visuals",
    "🐬 MySQL Database Manager (CRUD)"
])

# TAB 1: LEADERBOARDS & OVERVIEW
with tab1:
    st.subheader("📌 Assignment Core Leaderboards (Queried Live from MySQL)")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("##### 🥇 Top 5 Students by Overall Average")
        top5_avg = run_query("SELECT rno, name, total, avg FROM students ORDER BY avg DESC LIMIT 5")
        st.dataframe(top5_avg, use_container_width=True, hide_index=True)
        
        st.markdown("##### 🧮 Top 3 Students in Mathematics")
        top3_math = run_query("SELECT rno, name, math, avg FROM students ORDER BY math DESC, avg DESC LIMIT 3")
        st.dataframe(top3_math, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("##### 🌍 Top 10 Students in General Knowledge (GK)")
        top10_gk = run_query("SELECT rno, name, gk, avg FROM students ORDER BY gk DESC, avg DESC LIMIT 10")
        st.dataframe(top10_gk, use_container_width=True, hide_index=True)

    st.markdown("##### 📋 Complete Student Directory (`MySQL: student_portal.students`)")
    st.dataframe(df, use_container_width=True, hide_index=True)

# TAB 2: AUTOMATED ANOMALY DETECTION
with tab2:
    st.subheader("🚨 At-Risk Alert System: Subject Failure Anomalies")
    st.info(
        "**Anomaly Rule :** Flag all students who hold a passing overall average "
        "(`avg > 35`) but failed (`< 35`) in one or more individual subjects."
    )
    
    def find_failed_subjects(row):
        subjects = {'English': 'eng', 'Math': 'math', 'Science': 'sci', 'Computer': 'com', 'GK': 'gk'}
        failed = [f"{sub_name} ({row[col]})" for sub_name, col in subjects.items() if row[col] < 35]
        return ", ".join(failed)
    
    if not anomalies_df.empty:
        display_anomalies = anomalies_df.copy()
        display_anomalies["Failed Subject(s)"] = display_anomalies.apply(find_failed_subjects, axis=1)
        
        st.warning(f"⚠️ **{len(display_anomalies)} Students Flagged** for immediate academic intervention!")
        st.dataframe(
            display_anomalies[['rno', 'name', 'eng', 'math', 'sci', 'com', 'gk', 'total', 'avg', 'Failed Subject(s)']],
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("#### 🔍 Detailed Diagnostic Cards")
        cols = st.columns(3)
        for idx, (_, row) in enumerate(display_anomalies.iterrows()):
            with cols[idx % 3]:
                st.error(
                    f"**{row['name']} (Roll No: {row['rno']})**\n"
                    f"- **Overall Average:** {row['avg']}% (Total: {row['total']}/500)\n"
                    f"- **Critical Bottleneck:** {row['Failed Subject(s)']}"
                )
    else:
        st.success("No at-risk subject anomalies detected!")

    with st.expander("📉 View Students Failing Overall (Average <= 35)"):
        overall_fail = df[df['avg'] <= 35.0]
        st.dataframe(overall_fail, use_container_width=True, hide_index=True)

# TAB 3: INTERACTIVE MATPLOTLIB VISUALS
with tab3:
    st.subheader("📊 Interactive Visual Analytics Suite")
    
    viz_subtab1, viz_subtab2, viz_subtab3, viz_subtab4 = st.tabs([
        "1️⃣ Grouped Bar Chart (Top N Comparison)",
        "2️⃣ Class Average Histogram",
        "3️⃣ Subject Correlation Scatter Plot",
        "4️⃣ Individual Student Pie Chart"
    ])
    
    # 1. Grouped Bar Chart
    with viz_subtab1:
        st.markdown("#### Comparing Individual Subject Scores Across Top N Students")
        c_ctrl1, c_ctrl2 = st.columns([1, 2])
        with c_ctrl1:
            top_n = st.slider("Select Number of Top Students (N):", min_value=3, max_value=15, value=5)
            sort_by_col = st.selectbox("Rank Students By:", ["avg", "eng", "math", "sci", "com", "gk"], index=0)
        with c_ctrl2:
            selected_subjects = st.multiselect(
                "Select Subjects to Compare:",
                options=["eng", "math", "sci", "com", "gk"],
                default=["eng", "math", "sci", "com", "gk"]
            )
            
        if selected_subjects:
            subset = df.sort_values(by=sort_by_col, ascending=False).head(top_n)
            x = np.arange(len(subset))
            width = 0.8 / len(selected_subjects)
            
            fig, ax = plt.subplots(figsize=(11, 5))
            colors = ['#2563eb', '#f97316', '#10b981', '#8b5cf6', '#ec4899']
            
            for i, sub in enumerate(selected_subjects):
                offset = (i - len(selected_subjects) / 2) * width + width / 2
                ax.bar(x + offset, subset[sub], width, label=sub.upper(), color=colors[i % len(colors)])
                
            ax.set_xlabel("Student Name", fontweight="bold")
            ax.set_ylabel("Marks (0 - 100)", fontweight="bold")
            ax.set_title(f"Subject Score Comparison — Top {top_n} Students (Sorted by {sort_by_col.upper()})", fontweight="bold")
            ax.set_xticks(x)
            ax.set_xticklabels(subset["name"], rotation=25, ha="right")
            ax.set_ylim(0, 110)
            ax.axhline(35, color='red', linestyle='--', linewidth=1, label='Pass Mark (35)')
            ax.legend(loc="upper right", ncol=len(selected_subjects)+1)
            ax.grid(axis='y', linestyle=':', alpha=0.6)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("Please select at least one subject to plot.")

    # 2. Histogram with Adjustable Bin Slider
    with viz_subtab2:
        st.markdown("#### Visualizing the Distribution of Average Marks Across the Class")
        bins_count = st.slider("Adjust Histogram Bins:", min_value=3, max_value=20, value=5)
        
        fig2, ax2 = plt.subplots(figsize=(10, 4.5))
        counts, edges, patches = ax2.hist(df["avg"], bins=bins_count, color="#3b82f6", edgecolor="black", alpha=0.85)
        ax2.axvline(df["avg"].mean(), color="#ef4444", linestyle="--", linewidth=2, label=f"Class Mean ({df['avg'].mean():.1f}%)")
        ax2.axvline(35, color="#f59e0b", linestyle=":", linewidth=2, label="Passing Threshold (35%)")
        
        for count, patch in zip(counts, patches):
            if count > 0:
                ax2.annotate(
                    f"{int(count)}",
                    xy=(patch.get_x() + patch.get_width() / 2, count),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center", va="bottom", fontweight="bold"
                )
                
        ax2.set_xlabel("Average Marks Range (Bins)", fontweight="bold")
        ax2.set_ylabel("Number of Students", fontweight="bold")
        ax2.set_title(f"Class Average Distribution ({bins_count} Bins)", fontweight="bold")
        ax2.set_ylim(0, max(counts) * 1.18)
        ax2.legend()
        ax2.grid(axis='y', linestyle=':', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig2)

    # 3. Scatter Plot for Subject Correlations
    with viz_subtab3:
        st.markdown("#### Subject Correlation Analysis (Scatter Plot)")
        sc1, sc2, sc3 = st.columns(3)
        subject_map = {"Mathematics": "math", "Science": "sci", "English": "eng", "Computer": "com", "General Knowledge": "gk"}
        with sc1:
            x_label = st.selectbox("X-Axis Subject:", list(subject_map.keys()), index=0)
        with sc2:
            y_label = st.selectbox("Y-Axis Subject:", list(subject_map.keys()), index=1)
        with sc3:
            show_trend = st.checkbox("Show Linear Trendline & Anomalies", value=True)
            
        x_col = subject_map[x_label]
        y_col = subject_map[y_label]
        corr_val = df[x_col].corr(df[y_col])
        
        st.metric(f"Pearson Correlation ({x_label} vs. {y_label})", f"r = {corr_val:.3f}")
        
        fig3, ax3 = plt.subplots(figsize=(9, 5))
        is_anomaly = df["rno"].isin(anomalies_df["rno"]) if not anomalies_df.empty else pd.Series(False, index=df.index)
        
        ax3.scatter(
            df.loc[~is_anomaly, x_col],
            df.loc[~is_anomaly, y_col],
            color="#10b981", s=70, alpha=0.8, edgecolors="k", label="Regular Students"
        )
        ax3.scatter(
            df.loc[is_anomaly, x_col],
            df.loc[is_anomaly, y_col],
            color="#ef4444", s=110, marker="D", edgecolors="k", label="At-Risk Anomaly (Avg>35, Subj<35)"
        )
        
        if show_trend:
            m, b = np.polyfit(df[x_col], df[y_col], 1)
            x_vals = np.linspace(df[x_col].min(), df[x_col].max(), 100)
            ax3.plot(x_vals, m * x_vals + b, color="#1d4ed8", linestyle="--", linewidth=1.8, label=f"Trendline (y={m:.2f}x+{b:.1f})")
            for _, r_row in df.loc[is_anomaly].iterrows():
                ax3.annotate(r_row["name"], (r_row[x_col], r_row[y_col]), xytext=(6, 4), textcoords="offset points", fontsize=8.5, color="#b91c1c", fontweight="bold")
                
        ax3.axvline(35, color="gray", linestyle=":", alpha=0.7)
        ax3.axhline(35, color="gray", linestyle=":", alpha=0.7)
        ax3.set_xlabel(f"{x_label} Marks", fontweight="bold")
        ax3.set_ylabel(f"{y_label} Marks", fontweight="bold")
        ax3.set_title(f"{x_label} vs. {y_label} Marks Correlation (r = {corr_val:.2f})", fontweight="bold")
        ax3.legend()
        ax3.grid(True, linestyle=":", alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig3)

    # 4. Individual Student Pie Chart Breakdown
    with viz_subtab4:
        st.markdown("#### Individual Student Subject Contribution (Pie Chart)")
        student_list = df.apply(lambda r: f"{r['rno']} - {r['name']} (Avg: {r['avg']}%)", axis=1).tolist()
        selected_student_str = st.selectbox("Select Student:", student_list, index=min(14, len(student_list)-1))
        selected_rno = int(selected_student_str.split(" - ")[0])
        
        st_row = df[df["rno"] == selected_rno].iloc[0]
        subj_labels = ["English", "Mathematics", "Science", "Computer", "General Knowledge"]
        subj_scores = [st_row["eng"], st_row["math"], st_row["sci"], st_row["com"], st_row["gk"]]
        
        p_col1, p_col2 = st.columns([1.3, 1])
        with p_col1:
            fig4, ax4 = plt.subplots(figsize=(6.5, 6.5))
            explode = [0.08 if s < 35 else 0.01 for s in subj_scores]
            pie_colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]
            
            ax4.pie(
                subj_scores,
                labels=subj_labels,
                autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct * st_row['total'] / 100.0))})",
                startangle=140,
                explode=explode,
                colors=pie_colors,
                shadow=True,
                textprops=dict(color="black", fontweight="bold")
            )
            ax4.set_title(f"Subject Contribution for {st_row['name']} (Total: {st_row['total']}/500)", fontweight="bold")
            st.pyplot(fig4)
            
        with p_col2:
            st.markdown(f"##### 📄 Report Card: **{st_row['name']}**")
            st.write(f"- **Roll Number:** `{st_row['rno']}`")
            st.write(f"- **Total Marks:** `{st_row['total']} / 500`")
            st.write(f"- **Overall Average:** `{st_row['avg']}%`")
            
            score_table = pd.DataFrame({
                "Subject": subj_labels,
                "Marks (out of 100)": subj_scores,
                "Share of Total (%)": [f"{(s / st_row['total']) * 100:.1f}%" for s in subj_scores],
                "Status": ["❌ FAIL (<35)" if s < 35 else "✅ PASS" for s in subj_scores]
            })
            st.dataframe(score_table, use_container_width=True, hide_index=True)

# TAB 4: MYSQL DATABASE MANAGER (CRUD)
with tab4:
    st.subheader("🐬 MySQL Relational Record Manager (`PRIMARY KEY` & `CHECK` Constraints Enforced)")
    st.markdown(
        "Add student records directly into your MySQL `student_portal.students` table. "
        "MySQL 8.0+ enforces `PRIMARY KEY (rno)` and `CHECK (marks >= 0 AND marks <= 100)`."
    )
    
    with st.form("add_student_mysql_form"):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            new_rno = st.number_input("Roll Number (PRIMARY KEY):", min_value=1, value=int(df["rno"].max()) + 1, step=1)
            new_name = st.text_input("Student Full Name:", placeholder="e.g., Aamir Khan")
            new_eng = st.number_input("English Marks (0-100):", min_value=-10, max_value=120, value=75)
            new_math = st.number_input("Math Marks (0-100):", min_value=-10, max_value=120, value=80)
        with f_col2:
            new_sci = st.number_input("Science Marks (0-100):", min_value=-10, max_value=120, value=78)
            new_com = st.number_input("Computer Marks (0-100):", min_value=-10, max_value=120, value=82)
            new_gk = st.number_input("GK Marks (0-100):", min_value=-10, max_value=120, value=70)
            st.caption("💡 Tip: Enter a duplicate Roll No (triggers MySQL Error 1062) or marks > 100 (triggers MySQL Error 3819 CHECK constraint) to test validation!")
            
        submitted = st.form_submit_button("➕ Insert Record into MySQL")
        if submitted:
            if not new_name.strip():
                st.error("Student Name cannot be empty (`NOT NULL` constraint).")
            else:
                calc_total = int(new_eng + new_math + new_sci + new_com + new_gk)
                calc_avg = round(calc_total / 5.0, 2)
                try:
                    conn = get_db_connection(db_host, int(db_port), db_user, db_password, db_name)
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO students (rno, name, eng, math, sci, com, gk, total, avg)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (new_rno, new_name.strip(), new_eng, new_math, new_sci, new_com, new_gk, calc_total, calc_avg)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"✅ Successfully inserted {new_name} (Roll No: {new_rno}) into MySQL `{db_name}.students`!")
                    st.rerun()
                except Error as e:
                    st.error(f"🛑 **MySQL Constraint Violation (`mysql.connector.Error`):** `{e}`")
