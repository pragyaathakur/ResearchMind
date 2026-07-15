import streamlit as st
import time
from dotenv import load_dotenv
from agents import build_reader_agent, build_search_agent, critic_chain, writer_chain

load_dotenv()

# ── Helper function for content cleaning ─────────────────────────────────────
def to_str(value) -> str:
    if isinstance(value, str):
        return value
    if hasattr(value, "content"):
        return to_str(value.content)
    if isinstance(value, list):
        parts = [to_str(item) for item in value]
        return "\n".join(parts)
    return str(value)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Pipeline",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Theme CSS (From First Code) ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0f !important;
    color: #e8e6f0 !important;
}
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding: 2.5rem 3rem 4rem !important; max-width: 1100px; }

* { font-family: 'Syne', sans-serif; }
code, pre, .mono { font-family: 'Space Mono', monospace !important; }

.hero { text-align: center; padding: 3.5rem 0 2.5rem; }
.hero-badge {
    display: inline-block; font-family: 'Space Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.2em; text-transform: uppercase; color: #7b6af0;
    border: 1px solid #7b6af080; padding: 0.3rem 0.9rem; border-radius: 2px; margin-bottom: 1.2rem;
}
.hero h1 {
    font-size: clamp(2.4rem, 5vw, 3.8rem); font-weight: 800; line-height: 1.05;
    background: linear-gradient(135deg, #ffffff 0%, #a89ef7 55%, #6e5ce6 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 0.8rem;
}
.hero p { color: #7f7d99; font-size: 1rem; max-width: 520px; margin: 0 auto; line-height: 1.6; }

.input-card { background: #13121f; border: 1px solid #2a2840; border-radius: 12px; padding: 2rem 2.2rem; margin-bottom: 2rem; }

[data-testid="stTextInput"] input {
    background: #0d0c18 !important; border: 1px solid #2a2840 !important;
    border-radius: 8px !important; color: #e8e6f0 !important;
}
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #6e5ce6, #9b8af4) !important;
    color: #fff !important; border-radius: 8px !important; font-weight: 700 !important;
    width: 100%; transition: all 0.2s ease !important;
}

.pipeline-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; margin-bottom: 1.2rem; }
.stage-card {
    background: #13121f; border: 1px solid #2a2840; border-radius: 10px; padding: 1.4rem 1.6rem;
    position: relative; overflow: hidden;
}
.stage-card.active { border-color: #7b6af0; }
.stage-card.done { border-color: #4ade80; }
.stage-card.waiting { opacity: 0.45; }

.stage-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
.stage-label { font-family: 'Space Mono', monospace; font-size: 0.62rem; color: #7b6af0; text-transform: uppercase; }
.stage-title { font-size: 0.95rem; font-weight: 700; color: #e8e6f0; }
.stage-status { font-family: 'Space Mono', monospace; font-size: 0.7rem; color: #5f5d7a; }
.stage-card.done .stage-status { color: #4ade80; }

.result-panel { background: #13121f; border: 1px solid #2a2840; border-radius: 10px; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem; }
.result-panel-title { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #9593b0; border-bottom: 1px solid #1e1d2e; padding-bottom: 8px; margin-bottom: 12px; }
.result-panel-body { font-size: 0.92rem; line-height: 1.75; color: #c5c3db; white-space: pre-wrap; font-family: 'Space Mono', monospace; }
.feedback-panel { background: #0f1a14; border-color: #4ade8040; }
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">Multi-Agent System</div>
    <h1>Research Pipeline</h1>
    <p>Four specialised agents working in sequence to produce deep research on any topic.</p>
</div>
""", unsafe_allow_html=True)

# ── Logic: Session State ─────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = {}
if "running" not in st.session_state:
    st.session_state.running = False

# ── Input ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="input-card">', unsafe_allow_html=True)
col_inp, col_btn = st.columns([5, 1], vertical_alignment="bottom")
with col_inp:
    topic = st.text_input("Research Topic", placeholder="e.g. Quantum computing breakthroughs in 2025", key="topic_input")
with col_btn:
    run_btn = st.button("Run →")
st.markdown('</div>', unsafe_allow_html=True)

# ── Pipeline Visualizer Helper ───────────────────────────────────────────────
STAGES = [
    ("🔍", "STEP 01", "Search Agent", "search"),
    ("📄", "STEP 02", "Reader Agent", "reader"),
    ("✍️", "STEP 03", "Writer Chain", "writer"),
    ("🎯", "STEP 04", "Critic Chain", "critic"),
]

def render_pipeline():
    r = st.session_state.results
    running = st.session_state.running
    cards = []
    
    steps_list = ["search", "reader", "writer", "critic"]
    
    for i, (icon, label, title, key) in enumerate(STAGES):
        status = "Waiting"
        cls = "waiting"
        
        if key in r:
            status = "✓ Complete"
            cls = "done"
        elif running:
            # Find the first step not in results
            current_step = next((s for s in steps_list if s not in r), None)
            if key == current_step:
                status = "⟳ Running…"
                cls = "active"
        
        cards.append(f"""
        <div class="stage-card {cls}">
            <div class="stage-icon">{icon}</div>
            <div class="stage-label">{label}</div>
            <div class="stage-title">{title}</div>
            <div class="stage-status">{status}</div>
        </div>""")

    st.markdown(f'<div class="pipeline-grid">{cards[0]}{cards[1]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pipeline-grid">{cards[2]}{cards[3]}</div>', unsafe_allow_html=True)

render_pipeline()

# ── Execution Logic ──────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.error("Please enter a topic.")
    else:
        st.session_state.results = {}
        st.session_state.running = True
        st.rerun()

if st.session_state.running:
    topic_val = st.session_state.topic_input
    results = st.session_state.results

    try:
        # Step 1: Search
        if "search" not in results:
            search_agent = build_search_agent()
            sr = search_agent.invoke({"messages": [("user", f"Research: {topic_val}")]})
            results["search"] = to_str(sr["messages"][-1].content)
            st.session_state.results = results
            st.rerun()

        # Step 2: Reader (Fix applied here!)
        if "reader" not in results:
            reader_agent = build_reader_agent()
            rr = reader_agent.invoke({"messages": [("user", f"Scrape top info for: {topic_val}\n\nContext: {results['search'][:1000]}")]})
            results["reader"] = to_str(rr["messages"][-1].content)
            st.session_state.results = results
            st.rerun()

        # Step 3: Writer
        if "writer" not in results:
            context = f"Search: {results['search']}\nScraped: {results['reader']}"
            results["writer"] = to_str(writer_chain.invoke({"topic": topic_val, "research": context}))
            st.session_state.results = results
            st.rerun()

        # Step 4: Critic
        if "critic" not in results:
            results["critic"] = to_str(critic_chain.invoke({"report": results["writer"]}))
            st.session_state.results = results
            st.session_state.running = False
            st.rerun()

    except Exception as e:
        st.session_state.running = False
        st.error(f"Error: {e}")

# ── Results Display ──────────────────────────────────────────────────────────
r = st.session_state.results
if r:
    st.markdown('<hr style="border-color:#1e1d2e; margin: 2rem 0;">', unsafe_allow_html=True)
    
    if "writer" in r:
        st.markdown(f"""
        <div class="result-panel">
            <div class="result-panel-title">✍️ Final Research Report</div>
            <div class="result-panel-body">{r['writer']}</div>
        </div>
        """, unsafe_allow_html=True)

    if "critic" in r:
        st.markdown(f"""
        <div class="result-panel feedback-panel">
            <div class="result-panel-title">🎯 Critic Feedback</div>
            <div class="result-panel-body">{r['critic']}</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("View Raw Agent Logs"):
        if "search" in r:
            st.text_area("Search Logs", r["search"], height=150)
        if "reader" in r:
            st.text_area("Reader Logs", r["reader"], height=150)