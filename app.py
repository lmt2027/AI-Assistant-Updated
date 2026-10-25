"""AI Security Assistant: a demonstration Streamlit dashboard.

Security activity is synthetic sample data, not live monitoring.
AI explanations use an external OpenRouter free model when available.
"""
import html
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from database import (
    create_database, get_detected_alerts, get_reviews,
    save_detected_alert, save_review, seed_demo_alerts,
)
from securitychecker import check_failed_logins
from database import create_event_tables, seed_security_events, get_security_events
from event_detection import analyze_database_events
from ai_assistant import ask_ai, get_api_key, DEFAULT_MODEL

st.set_page_config(
    page_title="AI Security Assistant", page_icon="🛡️",
    layout="wide", initial_sidebar_state="expanded",
)
create_database()
seed_demo_alerts()
create_event_tables()
seed_security_events()

st.markdown("""
<style>
:root { --navy:#102748; --blue:#1975e9; }
[data-testid="stAppViewContainer"] { background:#f5f8fd; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#112e54,#0d223d); }
[data-testid="stSidebar"] * { color:#f4f8ff !important; }
[data-testid="stSidebar"] [role="radiogroup"] label { border-radius:9px; padding:8px 10px; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:#2169c9; }
.block-container { padding-top:1.1rem; padding-bottom:2.5rem; max-width:1700px; }
h1,h2,h3 { color:#102748 !important; letter-spacing:-.025em; }
[data-testid="stMetric"] { background:white; border:1px solid #e3eaf4; border-radius:12px; padding:12px; }
button[kind="primary"] { background:#176de0 !important; }
.hero { background:linear-gradient(110deg,#0d274b,#164a7b); color:white; padding:18px 24px; border-radius:13px; margin-bottom:16px; }
.hero-title { font-size:25px; font-weight:750; color:white; }
.hero-sub { color:#d5e5fb; font-size:13px; margin-top:4px; }
.hero-pill { float:right; font-size:12px; background:#285783; padding:6px 10px; border-radius:20px; }
.summary { border:1px solid var(--outline); background:var(--bg); border-radius:12px; padding:17px 16px; min-height:126px; }
.summary-number { font-size:36px; font-weight:800; color:#0c264a; line-height:1.25; }
.summary-label { font-size:15px; font-weight:700; color:var(--accent); }
.summary-note { font-size:12px; color:#4b617b; margin-top:5px; }
.section-head { color:#102748; font-size:20px; font-weight:750; margin:6px 0 12px; }
.alert-card { border-radius:11px; border:1px solid var(--outline); background:var(--bg); padding:12px 15px; margin:4px 0; min-height:125px; }
.alert-title { color:#102748; font-size:15px; font-weight:750; margin-bottom:5px; }
.alert-desc { color:#314c6c; font-size:13px; line-height:1.5; }
.alert-tag { display:inline-block; border-radius:7px; color:var(--accent); background:var(--tag); padding:4px 9px; font-size:12px; font-weight:750; margin-top:8px; }
.alert-time { font-size:11px; color:#63738a; margin-top:8px; }
.panel { background:#fff; border:1px solid #dfe7f2; border-radius:12px; padding:15px; margin-bottom:12px; }
.small-note { color:#5a6d85; font-size:12px; }
/* Keep wide model-generated tables from stretching the dashboard. */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 0; }
[data-testid="stChatMessageContent"] { min-width: 0; overflow-wrap: anywhere; }
[data-testid="stChatMessageContent"] table { display:block; max-width:100%; overflow-x:auto; white-space:normal; }
.chat-bubble { background:#f1f6fe; border:1px solid #e0eafb; border-radius:10px; padding:12px; font-size:13px; color:#193457; line-height:1.6; margin:10px 0; }
</style>
""", unsafe_allow_html=True)

PAGES = ["Home", "Security Alerts", "Security Checker", "Protection Tips", "Action History", "Test Data", "Ask Assistant"]
if "main_navigation" not in st.session_state:
    st.session_state.main_navigation = "Home"
if "navigation_target" in st.session_state:
    st.session_state.main_navigation = st.session_state.pop("navigation_target")

st.sidebar.markdown("## 🛡️ AI Security Assistant")
st.sidebar.caption("Your Partner for a Safer Business")
st.sidebar.divider()
page = st.sidebar.radio("MAIN MENU", PAGES, key="main_navigation")
st.sidebar.divider()
st.sidebar.caption("SYNTHETIC DATA · No live monitoring")


def navigate(destination):
    st.session_state.navigation_target = destination
    st.rerun()


def priority_style(priority):
    return {
        "High": ("#fff0f1", "#f3cbd0", "#c72836", "#ffd9dd", "🔴"),
        "Medium": ("#fff7e8", "#f5e4bc", "#ba6b00", "#ffe9b2", "🟠"),
        "Low": ("#edf5ff", "#d5e7ff", "#2068ce", "#dbeaff", "🔵"),
    }.get(priority, ("#edf5ff", "#d5e7ff", "#2068ce", "#dbeaff", "🔵"))




def render_assistant_panel():
    st.markdown('<div class="section-head">🤖 AI Security Assistant</div>', unsafe_allow_html=True)
    st.caption("Online OpenRouter free AI model · Answers use read-only synthetic SQLite records")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if not get_api_key():
        st.warning("AI is not connected yet. Set OPENROUTER_API_KEY to enable real model responses. No fake AI replies will be shown.")
    else:
        st.success("AI connection configured · Demo database context")
    for role, message in st.session_state.chat_history[-8:]:
        with st.chat_message(role):
            st.write(message)
    with st.form(f"assistant_form_{page}", clear_on_submit=True):
        question = st.text_input("Ask a question", placeholder="What happened in the sample data?")
        submitted = st.form_submit_button("Ask AI", use_container_width=True)
    if submitted and question.strip():
        history = st.session_state.chat_history[:]
        try:
            with st.spinner("Asking the AI assistant..."):
                answer = ask_ai(question.strip(), history=history)
        except Exception as exc:
            st.error(f"Could not get an AI response: {exc}")
        else:
            st.session_state.chat_history.extend([("user", question.strip()), ("assistant", answer)])
            st.rerun()
    st.caption("Suggested questions")
    for label, question in [
        ("What should I do first?", "Based on the saved sample alerts, what should I do first?"),
        ("Summarize test data", "Summarize the patterns in the synthetic security event database."),
    ]:
        if st.button(label, key=f"suggest_{page}_{label}", use_container_width=True):
            history = st.session_state.chat_history[:]
            try:
                with st.spinner("Asking the AI assistant..."):
                    answer = ask_ai(question, history=history)
            except Exception as exc:
                st.error(f"Could not get an AI response: {exc}")
            else:
                st.session_state.chat_history.extend([("user", question), ("assistant", answer)])
                st.rerun()


alerts = get_detected_alerts()
reviews = get_reviews()
reviewed_ids = {review[0] for review in reviews}
reviewed_detected = sum(f"detected_{alert[0]}" in reviewed_ids for alert in alerts)
needs_review = len(alerts) - reviewed_detected

if page == "Home":
    st.markdown('''<div class="hero"><span class="hero-pill">● Demo Mode</span>
      <div class="hero-title">🛡️ Security Overview</div>
      <div class="hero-sub">Understand your business security, review warnings, and choose the next step.</div>
    </div>''', unsafe_allow_html=True)
    if needs_review:
        st.warning(f"⚠️ {needs_review} detected warning(s) are waiting for review. Reviewing does not mean the issue is resolved.")
    else:
        st.info("All detected warnings have been reviewed. This does not establish that your systems are secure.")

    counts = {level: sum(str(a[2]).lower() == level.lower() for a in alerts) for level in ("High", "Medium", "Low")}
    cards = [
        ("🔺", "High Priority", counts["High"], "Needs your attention", "#fff0f1", "#f4cbd0", "#d12d3c"),
        ("❗", "Medium Priority", counts["Medium"], "Worth reviewing", "#fff8e9", "#f5e6c5", "#d2780b"),
        ("ℹ️", "Low Priority", counts["Low"], "Keep an eye on it", "#edf5ff", "#d6e7ff", "#246fe1"),
        ("✔", "Reviewed", reviewed_detected, "Recorded review actions", "#eaf8f0", "#cfeadd", "#178650"),
    ]
    cols = st.columns(4, gap="small")
    for col, (symbol, label, count, note, bg, outline, accent) in zip(cols, cards):
        with col:
            st.markdown(f'''<div class="summary" style="--bg:{bg};--outline:{outline};--accent:{accent}">
              <div class="summary-number">{symbol} {count}</div>
              <div class="summary-label">{label}</div><div class="summary-note">{note}</div>
            </div>''', unsafe_allow_html=True)
    st.write("")

    main_col, assistant_col = st.columns([3.4, 1.15], gap="large")
    with main_col:
        st.markdown('<div class="section-head">🔔 Recent Security Alerts</div>', unsafe_allow_html=True)
        st.caption("Latest saved demonstration warnings, with explanations and next steps.")
        for alert in alerts[:4]:
            alert_id, title, severity, explanation, recommendation, attempts, detected_at = alert
            bg, outline, accent, tag, symbol = priority_style(severity)
            card_col, button_col = st.columns([4.1, 1.2], gap="small")
            with card_col:
                st.markdown(f'''<div class="alert-card" style="--bg:{bg};--outline:{outline};--accent:{accent};--tag:{tag}">
                  <div class="alert-title">{symbol} {html.escape(title)}</div>
                  <div class="alert-desc">{html.escape(explanation)}</div>
                  <span class="alert-tag">{html.escape(severity)} Priority</span>
                  <div class="alert-time">Detected: {html.escape(detected_at)}</div>
                </div>''', unsafe_allow_html=True)
            with button_col:
                st.write("")
                if st.button("Review details", key=f"home_alert_{alert_id}", use_container_width=True):
                    st.session_state["focus_alert"] = alert_id
                    navigate("Security Alerts")
                if f"detected_{alert_id}" in reviewed_ids:
                    st.caption("✓ Reviewed")
                else:
                    st.caption("● Needs review")
        if len(alerts) > 4 and st.button("View all alerts →", key="all_alerts"):
            navigate("Security Alerts")
        st.write("")
        trend_col, areas_col, actions_col = st.columns([1.35, 1.05, 1.1], gap="small")
        with trend_col:
            st.markdown("#### 📊 Security Trend")
            st.caption("Saved warnings in the last 7 days")
            dates = [(datetime.now().date() - timedelta(days=i)) for i in range(6, -1, -1)]
            by_date = {day: 0 for day in dates}
            for a in alerts:
                try:
                    day = pd.to_datetime(a[6]).date()
                    if day in by_date:
                        by_date[day] += 1
                except (ValueError, TypeError):
                    pass
            chart_df = pd.DataFrame({"Date": pd.to_datetime(dates), "Alerts": [by_date[d] for d in dates]})
            st.line_chart(chart_df, x="Date", y="Alerts", height=220)
        with areas_col:
            st.markdown("#### 🧩 Affected Areas")
            st.caption("Grouped by alert title keywords")
            categories = {"Employee Accounts": 0, "Computers & Devices": 0, "Business Software": 0, "Other": 0}
            for a in alerts:
                name = a[1].lower()
                if any(word in name for word in ("login", "sign-in", "password", "employee", "account")):
                    categories["Employee Accounts"] += 1
                elif any(word in name for word in ("computer", "device", "endpoint")):
                    categories["Computers & Devices"] += 1
                elif any(word in name for word in ("software", "program", "update")):
                    categories["Business Software"] += 1
                else:
                    categories["Other"] += 1
            for category, count in categories.items():
                st.markdown(f"**{category}** · {count}")
        with actions_col:
            st.markdown("#### ⚡ Quick Actions")
            st.caption("Open a security tool")
            for label, target in [
                ("🛡️ Run Security Check", "Security Checker"),
                ("🔔 View All Alerts", "Security Alerts"),
                ("📚 Protection Tips", "Protection Tips"),
                ("📋 Action History", "Action History"),
                ("🗄️ Test Data", "Test Data"),
            ]:
                if st.button(label, key=f"quick_{target}", use_container_width=True):
                    navigate(target)
        st.write("")
        st.markdown("#### 🛡️ Alert Status Overview")
        status_a, status_b = st.columns(2)
        status_a.metric("Needs Review", needs_review)
        status_b.metric("Reviewed Detected Warnings", reviewed_detected)
        st.progress(reviewed_detected / len(alerts) if alerts else 0)
        st.caption(f"{reviewed_detected} of {len(alerts)} detected warnings reviewed. Review status is not resolution status.")
    with assistant_col:
        with st.container(border=True):
            st.markdown('<div class="section-head">🤖 AI Security Assistant</div>', unsafe_allow_html=True)
            st.caption("Free online AI · Answers use synthetic SQLite records")
            if get_api_key():
                st.success("AI connection configured")
            else:
                st.warning("Add your OpenRouter API key to enable AI responses.")
            st.write("Ask the assistant to explain warnings and recommend next steps in plain English.")
            if st.button("💬 Open AI Chat", key="home_open_chat", use_container_width=True, type="primary"):
                navigate("Ask Assistant")
            if "chat_history" in st.session_state and st.session_state.chat_history:
                st.caption("Your existing conversation is available on the Ask Assistant page.")

elif page == "Security Alerts":
    st.title("🔔 Security Alerts")
    st.caption("Review saved demonstration warnings. Marking a warning reviewed does not fix the underlying problem.")
    if not alerts:
        st.info("No warnings recorded yet. Try the Security Checker.")
    for alert in alerts:
        alert_id, title, severity, explanation, recommendation, attempts, detected_at = alert
        review_id = f"detected_{alert_id}"
        label = f"{'✅' if review_id in reviewed_ids else '⚠️'} {title} · {severity} · {detected_at} · ID {alert_id}"
        with st.expander(label, expanded=(st.session_state.get("focus_alert") == alert_id)):
            st.write("**What happened:**", explanation)
            st.write("**Suggested next step:**", recommendation)
            st.caption(f"Failed sign-in attempts (if applicable): {attempts}")
            if review_id in reviewed_ids:
                st.success("This warning has been reviewed.")
            elif st.button("Mark as Reviewed", key=f"review_{alert_id}"):
                save_review(review_id, title)
                st.rerun()
    st.session_state.pop("focus_alert", None)

elif page == "Security Checker":
    st.title("🛡️ Security Checker")
    st.caption("Enter sample sign-in data to test the demonstration detection rule.")
    with st.form("checker_form"):
        failed = st.number_input("Number of failed sign-in attempts", min_value=0, max_value=100000, value=0, step=1)
        run_check = st.form_submit_button("Analyze Sample Activity", type="primary")
    if run_check:
        warning = check_failed_logins(int(failed))
        if warning:
            alert_id = save_detected_alert(warning)
            st.error(f"{warning['severity']} Priority: {warning['title']}")
            st.write(warning["explanation"])
            st.write("**Recommended action:**", warning["recommendation"])
            st.success(f"Saved demonstration warning #{alert_id} to the database.")
        else:
            st.info("This sample did not meet the detection rule (5 or more failed sign-ins). That does not guarantee an account is safe.")
    st.caption("This tool does not read real sign-in logs or monitor live accounts. Each positive test creates a new saved warning.")

elif page == "Protection Tips":
    st.title("💡 Protection Tips")
    st.caption("Practical, general steps for small businesses")
    tips = [
        ("🔐 Use multi-factor authentication", "Add a second verification step to important accounts."),
        ("🔑 Use unique passwords", "Choose long, unique passwords and store them in a reputable password manager."),
        ("💻 Keep software updated", "Apply security updates from official vendors."),
        ("🧑‍💼 Review employee access", "Remove accounts that are no longer needed and limit unnecessary permissions."),
        ("💾 Maintain backups", "Keep protected backups and periodically test restoring them."),
        ("🎣 Watch for phishing", "Verify unexpected requests for passwords, payments, or sensitive information."),
    ]
    for title, description in tips:
        with st.container(border=True):
            st.subheader(title)
            st.write(description)

elif page == "Action History":
    st.title("📋 Action History")
    st.caption("A record of review actions saved in SQLite. Review does not mean remediation.")
    if reviews:
        history = pd.DataFrame(reviews, columns=["Alert ID", "Alert Name", "Reviewed At"])
        st.dataframe(history, use_container_width=True, hide_index=True)
        st.metric("Total Saved Reviews", len(reviews))
    else:
        st.info("No review actions have been saved yet.")


elif page == "Test Data":
    st.title("🗄️ Synthetic Security Event Database")
    st.caption("Events are generated locally, stored in SQLite, and are not connected to real accounts or devices.")
    events = get_security_events(limit=1000)
    st.metric("Stored Test Events", len(events))
    if events:
        frame = pd.DataFrame(events, columns=["ID", "Time", "Event Type", "Account", "Source IP", "Outcome", "Details"])
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button("Download synthetic events CSV", frame.to_csv(index=False).encode("utf-8"), "synthetic_security_events.csv", "text/csv")
    st.subheader("Run rule-based detection on the database")
    st.write("Looks for at least 5 failed sign-ins per account during the last 24 hours. Duplicate warnings for the same account and day are suppressed.")
    if st.button("Analyze Stored Events", type="primary"):
        created = analyze_database_events()
        if created:
            for ident, account, count in created:
                st.success(f"Saved warning #{ident}: {count} failed sign-ins for {account}.")
        else:
            st.info("No new qualifying warnings. Previously detected patterns will not create duplicates today.")
    st.caption("Only demo records are analyzed. No live systems are accessed.")

elif page == "Ask Assistant":
    st.title("💬 Ask Assistant")
    st.caption("Real AI-generated explanations grounded in synthetic database records. Requires a free OpenRouter API key.")
    render_assistant_panel()

st.divider()
st.caption("AI Security Assistant · Capstone demonstration · Synthetic SQLite events · Optional OpenRouter free-model integration · No live monitoring")