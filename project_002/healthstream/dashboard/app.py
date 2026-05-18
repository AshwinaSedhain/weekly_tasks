# Streamlit dashboard with six pages: overview, cost trends, fraud, hospitals, patients, live feed.
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PAGE_TITLE, REFRESH_INTERVAL
import api_client as api

st.set_page_config(
    page_title=PAGE_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem; }
</style>
""", unsafe_allow_html=True)


def fmt_currency(val: float) -> str:
    if val >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:.1f}K"
    return f"${val:.2f}"


with st.sidebar:
    st.title("Healthstream")
    st.caption("Healthcare Analytics Platform")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Overview", "Cost Trends", "Fraud Detection",
         "Hospital Performance", "Patient Risk", "Live Claims Feed"],
    )
    st.divider()

    auto_refresh = st.toggle("Auto-refresh", value=True)
    refresh_secs = st.slider("Refresh interval (s)", 10, 120, REFRESH_INTERVAL)

    st.divider()
    health = api.get_health()
    st.markdown(f"**API:** {'Online' if health.get('status') == 'healthy' else 'Offline'}")
    st.markdown(f"**DB:**  {'Connected' if health.get('database') == 'healthy' else 'Disconnected'}")

    if st.button("Refresh Now"):
        st.cache_data.clear()
        st.rerun()


if page == "Overview":
    st.title("Platform Overview")
    st.caption(f"Last updated: {pd.Timestamp.now().strftime('%H:%M:%S')}")

    summary = api.get_summary()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Claims",   f"{summary.get('total_claims', 0):,}")
    col2.metric("Total Amount",   fmt_currency(summary.get('total_amount', 0)))
    col3.metric("Avg Claim",      fmt_currency(summary.get('avg_amount', 0)))
    col4.metric("Fraud Detected", f"{summary.get('fraud_count', 0):,}")
    col5.metric("Fraud Rate",     f"{summary.get('fraud_rate', 0):.1f}%", delta_color="inverse")

    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("30-Day Cost Trend")
        trends = api.get_cost_trends(30)
        if trends:
            df = pd.DataFrame(trends)
            fig = px.area(
                df, x="summary_date", y="total_amount",
                color_discrete_sequence=["#2d6a9f"],
                labels={"total_amount": "Total Amount ($)", "summary_date": "Date"},
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available yet.")

    with col_right:
        st.subheader("Insurance Status Breakdown")
        ins = api.get_insurance_breakdown()
        if ins:
            df_ins = pd.DataFrame(ins)
            fig = px.pie(
                df_ins, names="insurance_status", values="count",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No insurance data available yet.")

    st.subheader("Top Diagnosis Codes")
    diag = api.get_diagnosis_breakdown(10)
    if diag:
        df_diag = pd.DataFrame(diag)
        fig = px.bar(
            df_diag, x="diagnosis_code", y="count",
            color="total_amount",
            color_continuous_scale="Blues",
            labels={"count": "Claim Count", "diagnosis_code": "ICD-10 Code"},
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


elif page == "Cost Trends":
    st.title("Healthcare Cost Trends")

    days   = st.slider("Days to display", 7, 90, 30)
    trends = api.get_cost_trends(days)

    if not trends:
        st.warning("No cost trend data available.")
    else:
        df = pd.DataFrame(trends)
        df["summary_date"] = pd.to_datetime(df["summary_date"])

        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(
                df, x="summary_date", y="total_amount",
                title="Total Daily Claims Amount",
                markers=True,
                color_discrete_sequence=["#2d6a9f"],
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                df, x="summary_date", y="total_claims",
                title="Daily Claim Volume",
                color="fraud_detected",
                color_continuous_scale="Reds",
                labels={"total_claims": "Claims", "fraud_detected": "Fraud"},
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["summary_date"], y=df["avg_claim_amount"],
            mode="lines+markers", name="Avg Claim Amount",
            line=dict(color="#27ae60", width=2),
        ))
        fig.add_trace(go.Bar(
            x=df["summary_date"], y=df["fraud_detected"],
            name="Fraud Detected", yaxis="y2",
            marker_color="rgba(231,76,60,0.5)",
        ))
        fig.update_layout(
            title="Average Claim Amount vs Fraud Detected",
            yaxis=dict(title="Avg Claim ($)"),
            yaxis2=dict(title="Fraud Count", overlaying="y", side="right"),
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Raw Data")
        st.dataframe(df.sort_values("summary_date", ascending=False), use_container_width=True)


elif page == "Fraud Detection":
    st.title("Fraud Detection")

    fraud_stats = api.get_fraud_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Alerts",    fraud_stats.get("total_alerts", 0))
    col2.metric("Unresolved",      fraud_stats.get("unresolved", 0))
    col3.metric("Resolution Rate", f"{fraud_stats.get('resolution_rate', 0):.1f}%")
    col4.metric("Critical Alerts", fraud_stats.get("by_severity", {}).get("CRITICAL", 0), delta_color="inverse")

    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Alerts by Severity")
        by_sev = fraud_stats.get("by_severity", {})
        if by_sev:
            fig = px.pie(
                names=list(by_sev.keys()),
                values=list(by_sev.values()),
                color_discrete_map={
                    "CRITICAL": "#c0392b", "HIGH": "#e74c3c",
                    "MEDIUM":   "#f39c12", "LOW":  "#27ae60",
                },
                hole=0.4,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Alerts by Type")
        by_type = fraud_stats.get("by_type", {})
        if by_type:
            fig = px.bar(
                x=list(by_type.keys()),
                y=list(by_type.values()),
                color=list(by_type.values()),
                color_continuous_scale="Reds",
                labels={"x": "Alert Type", "y": "Count"},
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Fraud Alerts")
    severity_filter = st.selectbox("Filter by severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    alerts = api.get_fraud_alerts(
        limit=100,
        severity=None if severity_filter == "All" else severity_filter,
    )
    if alerts:
        df_alerts = pd.DataFrame(alerts)
        cols_show = [c for c in ["alert_id", "claim_id", "fraud_score", "alert_type", "severity", "resolved", "created_at"] if c in df_alerts.columns]
        st.dataframe(
            df_alerts[cols_show].style.applymap(
                lambda v: "background-color: #fadbd8" if v in ["HIGH", "CRITICAL"] else "",
                subset=["severity"] if "severity" in cols_show else [],
            ),
            use_container_width=True,
        )
    else:
        st.info("No fraud alerts found.")


elif page == "Hospital Performance":
    st.title("Hospital Performance Comparison")

    hospitals = api.get_hospital_performance(30)
    if not hospitals:
        st.warning("No hospital data available.")
    else:
        df = pd.DataFrame(hospitals)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                df.head(15), x="hospital_name", y="performance_score",
                color="performance_score",
                color_continuous_scale="RdYlGn",
                title="Performance Score by Hospital",
                labels={"performance_score": "Score", "hospital_name": "Hospital"},
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                df, x="total_claims", y="total_amount",
                size="fraud_count",
                color="performance_score",
                hover_name="hospital_name",
                color_continuous_scale="RdYlGn",
                title="Claims Volume vs Total Amount",
                labels={"total_claims": "Total Claims", "total_amount": "Total Amount ($)"},
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Hospital Rankings")
        df_display = df[["hospital_name", "state", "total_claims", "total_amount", "fraud_count", "performance_score"]].copy()
        df_display["total_amount"]     = df_display["total_amount"].apply(lambda x: f"${x:,.0f}")
        df_display["performance_score"]= df_display["performance_score"].apply(lambda x: f"{x:.1f}")
        st.dataframe(df_display, use_container_width=True)


elif page == "Patient Risk":
    st.title("Patient Risk Analytics")

    threshold = st.slider("Risk score threshold", 0.0, 1.0, 0.7, 0.05)
    patients  = api.get_high_risk_patients(threshold=threshold, limit=100)

    if not patients:
        st.info(f"No patients with risk score above {threshold}")
    else:
        df = pd.DataFrame(patients)

        col1, col2, col3 = st.columns(3)
        col1.metric("High-Risk Patients", len(df))
        col2.metric("Avg Risk Score", f"{df['risk_score'].mean():.3f}" if "risk_score" in df.columns else "N/A")
        if "insurance_type" in df.columns:
            col3.metric("Uninsured", (df["insurance_type"] == "UNINSURED").sum())

        col_left, col_right = st.columns(2)
        with col_left:
            if "risk_score" in df.columns:
                fig = px.histogram(df, x="risk_score", nbins=20, title="Risk Score Distribution",
                                   color_discrete_sequence=["#e74c3c"])
                st.plotly_chart(fig, use_container_width=True)

        with col_right:
            if "state" in df.columns:
                state_counts = df["state"].value_counts().head(10).reset_index()
                state_counts.columns = ["state", "count"]
                fig = px.bar(state_counts, x="state", y="count", title="High-Risk Patients by State",
                             color="count", color_continuous_scale="Reds")
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("High-Risk Patient List")
        cols_show = [c for c in ["patient_id", "first_name", "last_name", "state", "insurance_type", "risk_score"] if c in df.columns]
        st.dataframe(df[cols_show].sort_values("risk_score", ascending=False), use_container_width=True)


elif page == "Live Claims Feed":
    st.title("Live Claims Feed")
    st.caption("Most recent claims from the pipeline")

    limit  = st.slider("Number of claims to display", 10, 200, 50)
    claims = api.get_latest_claims(limit=limit)

    if not claims:
        st.warning("No claims data available.")
    else:
        df = pd.DataFrame(claims)

        def highlight_fraud(row):
            if row.get("is_fraud"):
                return ["background-color: #fadbd8"] * len(row)
            return [""] * len(row)

        cols_show = [c for c in ["claim_id", "patient_id", "hospital_id", "diagnosis_code",
                                  "claim_amount", "insurance_status", "is_fraud", "fraud_score", "claim_date"]
                     if c in df.columns]
        st.dataframe(df[cols_show].style.apply(highlight_fraud, axis=1),
                     use_container_width=True, height=600)

        col1, col2 = st.columns(2)
        with col1:
            if "claim_amount" in df.columns:
                fig = px.histogram(df, x="claim_amount", nbins=30, title="Claim Amount Distribution",
                                   color_discrete_sequence=["#2d6a9f"])
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "insurance_status" in df.columns:
                status_counts = df["insurance_status"].value_counts().reset_index()
                status_counts.columns = ["status", "count"]
                fig = px.pie(status_counts, names="status", values="count",
                             title="Insurance Status Distribution", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)


if auto_refresh:
    time.sleep(refresh_secs)
    st.cache_data.clear()
    st.rerun()
