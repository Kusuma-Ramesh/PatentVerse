import streamlit as st
import sys
import os
from datetime import datetime

# Maintain existing logic for backend imports
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from agents.patent_agent import PatentAgent
from agents.risk_agent import RiskAgent
from services.gemini_service import generate_innovation

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="PatentVerse | Mission Control",
    page_icon="🕵🏼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# LOAD CUSTOM CSS
# =========================================================
def load_css(file_name: str):
    css_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("styles.css")

# =========================================================
# HELPERS (presentation only — backend logic untouched)
# =========================================================
def risk_clean(level: str) -> str:
    return (level or "medium").strip().lower()


def risk_pill_class(level: str) -> str:
    return {"low": "risk-low", "medium": "risk-medium", "high": "risk-high"}.get(risk_clean(level), "risk-medium")


def overall_risk(risks: dict) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    levels = [risk_clean(v) for v in risks.values()]
    return max(levels, key=lambda l: order.get(l, 1)).capitalize() if levels else "Medium"


def risk_to_pct(level: str) -> int:
    return {"low": 28, "medium": 58, "high": 88}.get(risk_clean(level), 58)


def innovation_score(text: str) -> int:
    return max(15, min(38 + (len(text or "") // 25), 97))


def novelty_score(patents: list) -> int:
    return max(20, min(92 - (len(patents) * 6 if patents else 0), 96))


def market_score(risks: dict, inno: int) -> int:
    bonus = {"low": 24, "medium": 8, "high": -14}.get(risk_clean(risks.get("Market Risk", "medium")), 8)
    return max(15, min(55 + bonus + (inno - 50) // 3, 96))


def recommendation(overall, novelty, market):
    o = overall.lower()
    if o == "high":
        return "HIGH RISK — FURTHER RESEARCH REQUIRED", "high"
    if o == "low" and novelty >= 60 and market >= 60:
        return "PROCEED TO PATENT FILING", "low"
    if novelty < 40:
        return "REFINE IDEA — LOW NOVELTY DETECTED", "medium"
    return "PROMISING — RECOMMEND EXPERT REVIEW", "medium"


def parse_risks(risk_text: str) -> dict:
    """
    Parses risk_agent.analyze_risk() output into a clean {Key: Value} dict.
    Handles both line-separated ("Patent Risk: High\\nMarket Risk: Low")
    and comma-separated ("Patent Risk: High, Market Risk: Low, ...") formats,
    and normalizes key casing (e.g. "market risk" -> "Market Risk").
    """
    risks = {}
    segments = []
    for line in str(risk_text).split("\n"):
        segments.extend(line.split(","))

    for segment in segments:
        segment = segment.strip()
        if ":" not in segment:
            continue
        key, value = segment.split(":", 1)
        key = key.strip().title()
        value = value.strip().capitalize()
        if key and value:
            risks[key] = value

    return risks


def friendly_error(exc: Exception) -> str:
    """Turns a raw backend exception into a short, human-readable message."""
    msg = str(exc)
    if "ResourceExhausted" in msg or "429" in msg or "quota" in msg.lower():
        return (
            "Gemini API daily free-tier quota has been used up for this project "
            "(the underlying AI service, not PatentVerse itself). It resets automatically — "
            "try again later, or switch to a paid Gemini API key in services/gemini_service.py."
        )
    return "This agent ran into an unexpected error and was skipped for this run."


def agent_trust(risks: dict):
    """Mock trust scores per agent for the Trust Monitor panel."""
    patent_t = 100 - risk_to_pct(risks.get("Patent Risk", "Medium")) * 0.3
    market_t = 100 - risk_to_pct(risks.get("Market Risk", "Low")) * 0.3
    tech_t = 100 - risk_to_pct(risks.get("Technical Risk", "Medium")) * 0.3
    return {
        "Patent": round(patent_t, 1),
        "Innovation": 96.0,
        "Risk": round((patent_t + market_t + tech_t) / 3, 1),
    }


# =========================================================
# SESSION STATE INIT
# =========================================================
if "pv_logs" not in st.session_state:
    st.session_state["pv_logs"] = []
if "pv_runs" not in st.session_state:
    st.session_state["pv_runs"] = 0
if "pv_errors" not in st.session_state:
    st.session_state["pv_errors"] = {}

risks_current = st.session_state.get("analysis_data", {}).get("risks", {})
trust = agent_trust(risks_current) if risks_current else {"Patent": 100.0, "Innovation": 100.0, "Risk": 100.0}
alert_high = any(risk_clean(v) == "high" for v in risks_current.values()) if risks_current else False

# =========================================================
# TOP BAR
# =========================================================
now_str = datetime.now().strftime("%H:%M:%S")
st.markdown(
    f"""
    <div class="topbar">
        <div class="topbar-logo">🧠 PATENT<span>VERSE</span></div>
        <div class="topbar-pills">
            <span class="pill pill-green"><span class="pill-dot"></span>3 ACTIVE AGENTS</span>
            <span class="pill {'pill-red' if alert_high else 'pill-green'}"><span class="pill-dot"></span>{'1 ALERT' if alert_high else '0 ALERTS'}</span>
            <span class="pill">+ {st.session_state['pv_runs']} ANALYSES RUN</span>
            <span class="pill-clock">{now_str}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# LAYOUT — LEFT / CENTER / RIGHT
# =========================================================
left, center, right = st.columns([1.05, 2.6, 1.05])

# ---------------------------------------------------------
# LEFT PANEL — Agent Monitor + Run Analysis + Prediction Engine
# ---------------------------------------------------------
with left:
    st.markdown('<div class="panel"><div class="panel-title"><span class="dot">●</span> AGENT MONITOR</div>', unsafe_allow_html=True)

    for name, label in [("Patent", "PatentAgent"), ("Innovation", "InnovationAgent"), ("Risk", "RiskAgent")]:
        t = trust.get(name, 100.0)
        st.markdown(
            f"""
            <div class="agent-card">
                <div class="agent-card-head">
                    <span class="agent-name">{label}</span>
                    <span class="badge badge-active">ACTIVE</span>
                </div>
                <div class="agent-meta">Trust: {t} | Events: {st.session_state['pv_runs']}</div>
                <div class="trust-track"><div class="trust-fill" style="width:{t}%;"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel"><div class="panel-title"><span class="dot">▸</span> RUN ANALYSIS</div>', unsafe_allow_html=True)
    idea = st.text_area(
        "idea",
        placeholder="Describe your invention idea...",
        height=130,
        label_visibility="collapsed",
    )
    analyze_clicked = st.button("⚡ Analyze Idea")
    st.markdown("</div>", unsafe_allow_html=True)

    if risks_current:
        st.markdown('<div class="panel"><div class="panel-title"><span class="dot">▸</span> PREDICTION ENGINE</div>', unsafe_allow_html=True)
        for risk_name in ["Patent Risk", "Market Risk", "Technical Risk"]:
            level = risks_current.get(risk_name, "Medium")
            pct = risk_to_pct(level)
            cls = risk_clean(level)
            st.markdown(
                f"""
                <div class="predict-row">
                    <span class="predict-label">{risk_name}</span>
                    <span class="predict-value {cls}">{pct}%</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# BACKEND EXECUTION (UNCHANGED LOGIC)
# ---------------------------------------------------------
if analyze_clicked:
    if not idea or len(idea.strip()) < 10:
        st.toast("⚠️ Please provide a more detailed description for the agents.", icon="⚠️")
    else:
        run_errors = {}

        with st.spinner("Agents processing..."):

            # ---- Patent Agent ----
            try:
                patent_agent = PatentAgent()
                patents = patent_agent.search_patents(idea)
            except Exception as e:
                patents = []
                run_errors["Patent Agent"] = friendly_error(e)

            # ---- Innovation Agent (Gemini) ----
            try:
                innovations = generate_innovation(idea)
            except Exception as e:
                innovations = ""
                run_errors["Innovation Agent"] = friendly_error(e)

            # ---- Risk Agent ----
            try:
                risk_agent = RiskAgent()
                risk_text = risk_agent.analyze_risk(idea)
                risks = parse_risks(risk_text)
            except Exception as e:
                risks = {}
                run_errors["Risk Agent"] = friendly_error(e)

        st.session_state["analysis_data"] = {
            "patents": patents,
            "innovations": innovations,
            "risks": risks,
        }
        st.session_state["pv_idea"] = idea
        st.session_state["pv_errors"] = run_errors
        st.session_state["pv_runs"] += 1

        if run_errors:
            failed = ", ".join(run_errors.keys())
            st.session_state["pv_logs"].insert(
                0,
                f"{datetime.now().strftime('%H:%M:%S')} — Analysis run #{st.session_state['pv_runs']} — "
                f"idea: \"{idea[:48]}{'...' if len(idea) > 48 else ''}\" — ⚠ {failed} unavailable",
            )
        else:
            st.session_state["pv_logs"].insert(
                0,
                f"{datetime.now().strftime('%H:%M:%S')} — Analysis run #{st.session_state['pv_runs']} — idea: \"{idea[:48]}{'...' if len(idea) > 48 else ''}\"",
            )
        st.rerun()

# ---------------------------------------------------------
# CENTER PANEL — Tabs
# ---------------------------------------------------------
with center:
    tab_overview, tab_patents, tab_innovations, tab_risks, tab_logs = st.tabs(
        ["Overview", "Patents", "Innovations", "Risks", "Logs"]
    )

    data = st.session_state.get("analysis_data")

    # ---------- OVERVIEW ----------
    with tab_overview:
        if not data:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="icon">🛰️</div>
                    <div>NO ANALYSIS RUNNING</div>
                    <div style="font-size:0.72rem; color:#4B5870;">Enter an idea and click Analyze Idea to begin</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            run_errors = st.session_state.get("pv_errors", {})
            if run_errors:
                for agent_name, msg in run_errors.items():
                    st.warning(f"**{agent_name} unavailable:** {msg}")

            patents = data["patents"]
            innovations = data["innovations"]
            risks = data["risks"]
            inno = innovation_score(innovations)
            nov = novelty_score(patents)
            mkt = market_score(risks, inno)
            ov_risk = overall_risk(risks)

            st.markdown(
                f"""
                <div class="kpi-grid">
                    <div class="kpi-card"><div class="kpi-label">📄 Similar Patents</div><div class="kpi-value">{len(patents) if patents else 0}</div></div>
                    <div class="kpi-card"><div class="kpi-label">💡 Innovation Score</div><div class="kpi-value">{inno}</div></div>
                    <div class="kpi-card"><div class="kpi-label">⚠ Risk Level</div><div class="kpi-value{' is-long' if len(str(ov_risk)) > 10 else ''}">{ov_risk}</div></div>
                    <div class="kpi-card"><div class="kpi-label">📈 Market Potential</div><div class="kpi-value">{mkt}</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="workflow-strip">
                    <div class="workflow-node done">💭 IDEA</div>
                    <div class="workflow-arrow-h">→</div>
                    <div class="workflow-node done">🔍 PATENT AGENT</div>
                    <div class="workflow-arrow-h">→</div>
                    <div class="workflow-node done">💡 INNOVATION AGENT</div>
                    <div class="workflow-arrow-h">→</div>
                    <div class="workflow-node done">⚖️ RISK AGENT</div>
                    <div class="workflow-arrow-h">→</div>
                    <div class="workflow-node done">🏆 VERDICT</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            rec_text, rec_cls = recommendation(ov_risk, nov, mkt)
            rec_colors = {
                "low": ("rgba(16,185,129,0.15)", "#10B981"),
                "medium": ("rgba(245,158,11,0.15)", "#F59E0B"),
                "high": ("rgba(239,68,68,0.15)", "#EF4444"),
            }
            bg, fg = rec_colors.get(rec_cls, rec_colors["medium"])

            st.markdown(
                f"""
                <div class="verdict-card">
                    <div class="verdict-title">🧠 AI VERDICT</div>
                    <div style="display:flex; gap:12px; flex-wrap:wrap;">
                        <div class="verdict-metric" style="flex:1; min-width:120px;">
                            <div class="label">Novelty Score</div><div class="value">{nov}/100</div>
                        </div>
                        <div class="verdict-metric" style="flex:1; min-width:120px;">
                            <div class="label">Market Potential</div><div class="value">{mkt}/100</div>
                        </div>
                        <div class="verdict-metric" style="flex:1; min-width:120px;">
                            <div class="label">Patent Risk</div><div class="value">{risks.get("Patent Risk", "—")}</div>
                        </div>
                    </div>
                    <div class="recommendation-banner" style="background:{bg}; color:{fg};">{rec_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            report_md = f"""# PatentVerse Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Idea
{st.session_state.get('pv_idea','')}

## Metrics
- Similar Patents: {len(patents) if patents else 0}
- Innovation Score: {inno}/100
- Risk Level: {ov_risk}
- Market Potential: {mkt}/100

## Risks
{chr(10).join(f"- {k}: {v}" for k, v in risks.items())}

## Innovations
{innovations}

## Recommendation
{rec_text}
"""
            st.download_button(
                "⬇ DOWNLOAD REPORT",
                data=report_md,
                file_name=f"PatentVerse_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )

    # ---------- PATENTS ----------
    with tab_patents:
        if not data:
            st.markdown('<div class="empty-state"><div class="icon">📄</div>RUN AN ANALYSIS TO VIEW PATENTS</div>', unsafe_allow_html=True)
        else:
            patents = data["patents"]
            if patents:
                for p in patents:
                    st.markdown(f'<div class="patent-card">🔎 {p}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state">NO SIMILAR PATENTS FOUND</div>', unsafe_allow_html=True)

    # ---------- INNOVATIONS ----------
    with tab_innovations:
        if not data:
            st.markdown('<div class="empty-state"><div class="icon">💡</div>RUN AN ANALYSIS TO VIEW INNOVATIONS</div>', unsafe_allow_html=True)
        elif not str(data["innovations"]).strip():
            st.markdown(
                '<div class="empty-state"><div class="icon">⚠️</div>INNOVATION AGENT UNAVAILABLE THIS RUN'
                '<div style="font-size:0.7rem; color:#4B5870;">See the warning on the Overview tab for details</div></div>',
                unsafe_allow_html=True,
            )
        else:
            innovations = data["innovations"]
            colors = ["inn-a", "inn-b", "inn-c"]
            lines = [l.strip() for l in str(innovations).split("\n") if l.strip()] or [str(innovations)]
            for i, line in enumerate(lines):
                st.markdown(f'<div class="innovation-card {colors[i % len(colors)]}">💡 {line}</div>', unsafe_allow_html=True)

    # ---------- RISKS ----------
    with tab_risks:
        if not data:
            st.markdown('<div class="empty-state"><div class="icon">⚖️</div>RUN AN ANALYSIS TO VIEW RISK BREAKDOWN</div>', unsafe_allow_html=True)
        else:
            risks = data["risks"]
            for k, v in risks.items():
                st.markdown(
                    f"""
                    <div class="risk-row">
                        <span class="risk-name">{k}</span>
                        <span class="risk-pill {risk_pill_class(v)}">{v.upper()}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ---------- LOGS ----------
    with tab_logs:
        logs = st.session_state["pv_logs"]
        if not logs:
            st.markdown('<div class="empty-state"><div class="icon">🗒️</div>NO LOG ENTRIES YET</div>', unsafe_allow_html=True)
        else:
            for entry in logs:
                ts, _, msg = entry.partition(" — ")
                st.markdown(f'<div class="log-line"><span class="ts">{ts}</span>{msg}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# RIGHT PANEL — Alerts / Trust Monitor / Pipeline / Meta
# ---------------------------------------------------------
with right:
    st.markdown('<div class="panel"><div class="panel-title"><span class="dot">●</span> ALERTS</div>', unsafe_allow_html=True)
    if alert_high:
        high_names = [k for k, v in risks_current.items() if risk_clean(v) == "high"]
        st.markdown(
            f'<div class="alert-banner alert-high">⚠ RISK [HIGH] — {", ".join(high_names)} flagged as high risk</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="alert-none">No alerts</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel"><div class="panel-title"><span class="dot">●</span> TRUST MONITOR</div>', unsafe_allow_html=True)
    bar_nodes = "".join(
        f'<div class="trust-bar-wrap"><div class="trust-bar" style="height:{val}%;"></div>'
        f'<div class="trust-bar-label">{name}</div></div>'
        for name, val in trust.items()
    )
    st.markdown(f'<div class="trust-chart">{bar_nodes}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel"><div class="panel-title"><span class="dot">●</span> PIPELINE STATUS</div>', unsafe_allow_html=True)
    pipeline_state = "COMPLETE" if st.session_state.get("analysis_data") else "IDLE"
    st.markdown(
        f"""
        <div class="pipeline-row"><span class="pipeline-dot"></span> Idea Intake — Ready</div>
        <div class="pipeline-row"><span class="pipeline-dot"></span> Patent Search — {pipeline_state}</div>
        <div class="pipeline-row"><span class="pipeline-dot"></span> Innovation Gen — {pipeline_state}</div>
        <div class="pipeline-row"><span class="pipeline-dot"></span> Risk Scoring — {pipeline_state}</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel"><div class="panel-title"><span class="dot">●</span> SYSTEM INFO</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="meta-row"><span>Model</span><span>Gemini</span></div>
        <div class="meta-row"><span>Mode</span><span>Multi-Agent</span></div>
        <div class="meta-row"><span>Runs</span><span>{st.session_state['pv_runs']}</span></div>
        <div class="meta-row"><span>Last Sync</span><span>{now_str}</span></div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)