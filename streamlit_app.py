import streamlit as st
import asyncio, time, json

from app.src.services.serper import get_serper_responses
from app.src.services.scrapper import run_scraping_pipeline
from app.src.services.prelim import run_haiku_analysis
from app.src.services.consolidator import run_consolidator
from app.src.services.writer import run_writer

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="SEO Writer", page_icon="✦", layout="wide")

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Merriweather:ital,wght@0,400;0,700;1,400&display=swap');

/* ── Reset Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] > div { background: #0f0f11; padding: 2rem 1.5rem; }
section[data-testid="stSidebar"] * { color: #e5e7eb !important; }

/* ── Sidebar inputs ── */
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input {
    background: #1c1c21 !important;
    border: 1px solid #2e2e38 !important;
    border-radius: 8px !important;
    color: #f9fafb !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] .stTextInput input:focus,
section[data-testlit="stSidebar"] .stNumberInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
}
section[data-testid="stSidebar"] label { font-size: 0.78rem !important; font-weight: 600 !important; letter-spacing: .05em !important; text-transform: uppercase !important; color: #9ca3af !important; }
section[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: opacity .2s !important;
}
section[data-testid="stSidebar"] .stButton button:hover { opacity: .88 !important; }

/* ── Main canvas ── */
.main-canvas {
    max-width: 860px;
    margin: 0 auto;
    padding: 3.5rem 2rem 6rem;
    font-family: 'Inter', sans-serif;
}

/* ── Article typography ── */
.art-label {
    display: inline-block;
    background: #ede9fe;
    color: #6d28d9;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    border-radius: 999px;
    padding: 3px 12px;
    margin-bottom: 1rem;
}
.art-h1 {
    font-family: 'Merriweather', serif;
    font-size: clamp(1.9rem, 4vw, 2.7rem);
    font-weight: 700;
    line-height: 1.25;
    color: #0f0f11;
    margin: 0 0 1.1rem;
}
.art-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.83rem;
    color: #6b7280;
    margin-bottom: 2rem;
}
.art-meta span { display: flex; align-items: center; gap: .3rem; }
.art-divider { border: none; border-top: 1px solid #e5e7eb; margin: 2rem 0; }
.art-intro {
    font-family: 'Merriweather', serif;
    font-size: 1.08rem;
    line-height: 1.85;
    color: #374151;
    border-left: 4px solid #6366f1;
    padding-left: 1.3rem;
    margin-bottom: 2.5rem;
}

/* ── Section headings ── */
.art-h2 {
    font-family: 'Inter', sans-serif;
    font-size: 1.45rem;
    font-weight: 800;
    color: #111827;
    margin: 2.5rem 0 0.65rem;
    padding-bottom: .4rem;
    border-bottom: 2px solid #f3f4f6;
}
.art-h3 {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #1f2937;
    margin: 1.8rem 0 0.5rem;
}
.art-p {
    font-size: 1rem;
    line-height: 1.85;
    color: #374151;
    margin-bottom: 1rem;
}

/* ── Conclusion box ── */
.art-conclusion {
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border-left: 5px solid #22c55e;
    border-radius: 12px;
    padding: 1.5rem 1.7rem;
    margin-top: 2.5rem;
    font-size: 1rem;
    line-height: 1.85;
    color: #14532d;
}
.art-conclusion-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #16a34a;
    margin-bottom: .5rem;
}

/* ── FAQ ── */
.faq-wrap { margin-top: 1rem; }
.faq-item {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin-bottom: .8rem;
    background: #fff;
    transition: box-shadow .2s;
}
.faq-item:hover { box-shadow: 0 4px 16px rgba(0,0,0,.07); }
.faq-q {
    font-weight: 700;
    font-size: .97rem;
    color: #111827;
    margin-bottom: .5rem;
    display: flex;
    gap: .6rem;
    align-items: flex-start;
}
.faq-q::before { content: "Q"; background:#6366f1; color:#fff; border-radius:4px; padding:1px 6px; font-size:.78rem; flex-shrink:0; margin-top:2px; }
.faq-a { font-size: .93rem; line-height: 1.75; color: #4b5563; padding-left: 1.5rem; }

/* ── SEO card ── */
.seo-card {
    background: #fafafa;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin: 2rem 0;
}
.seo-card-title { font-size: .72rem; font-weight: 700; letter-spacing:.1em; text-transform:uppercase; color:#6b7280; margin-bottom:1rem; }
.seo-row { display:flex; gap:.7rem; margin-bottom:.55rem; font-size:.88rem; flex-wrap:wrap; align-items:baseline; }
.seo-key { font-weight:600; color:#374151; min-width:140px; flex-shrink:0; }
.seo-val { color:#4b5563; }
.seo-val code { background:#ede9fe; color:#6d28d9; border-radius:4px; padding:1px 7px; font-size:.82rem; }
.kw-pill {
    display:inline-block;
    background:#f3f4f6;
    color:#374151;
    border:1px solid #e5e7eb;
    border-radius:999px;
    padding:2px 11px;
    font-size:.78rem;
    font-weight:500;
    margin:2px;
}

/* ── Links panel ── */
.links-grid { display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:1rem; }
.link-card {
    background:#fff;
    border:1px solid #e5e7eb;
    border-radius:10px;
    padding:.9rem 1rem;
    font-size:.85rem;
}
.link-card .anchor { font-weight:600; color:#6366f1; margin-bottom:.25rem; }
.link-card .hint { color:#6b7280; font-size:.8rem; line-height:1.5; }
.link-card .badge {
    display:inline-block;
    background:#f3f4f6;
    color:#9ca3af;
    border-radius:999px;
    padding:1px 9px;
    font-size:.72rem;
    margin-top:.4rem;
}

/* ── Progress pipeline ── */
.pipeline-step {
    display:flex;
    align-items:center;
    gap:.75rem;
    padding:.6rem .9rem;
    border-radius:8px;
    font-size:.88rem;
    font-weight:500;
    margin-bottom:.4rem;
    transition: background .3s;
}
.step-done  { background:#f0fdf4; color:#15803d; }
.step-active{ background:#eff6ff; color:#1d4ed8; }
.step-wait  { background:#f9fafb; color:#9ca3af; }

/* ── Empty state ── */
.empty-state {
    text-align:center;
    padding:5rem 2rem;
    color:#9ca3af;
}
.empty-state .icon { font-size:3rem; margin-bottom:1rem; }
.empty-state h3 { font-size:1.2rem; font-weight:700; color:#6b7280; margin-bottom:.5rem; }
.empty-state p { font-size:.9rem; line-height:1.6; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def g(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key, default)
    return obj.get(key, default) if isinstance(obj, dict) else default


STEPS = [
    ("🔍", "Fetching search results"),
    ("🕸️", "Scraping source pages"),
    ("🤖", "Analysing content"),
    ("📐", "Building blueprint"),
    ("✍️", "Writing article"),
]


def run_pipeline(topic: str, length: int, step_box):
    fns = [
        lambda: get_serper_responses(topic),
        lambda: run_scraping_pipeline(st.session_state._s0),
        lambda: asyncio.run(run_haiku_analysis(st.session_state._s1, topic)),
        lambda: asyncio.run(run_consolidator(st.session_state._s2, topic, length)),
        lambda: asyncio.run(run_writer(st.session_state._s3, length)),
    ]
    keys = ["_s0", "_s1", "_s2", "_s3", "_s4"]

    for i, fn in enumerate(fns):
        # render pipeline steps UI
        html = ""
        for j, (icon, label) in enumerate(STEPS):
            if j < i:
                cls = "step-done";   tick = "✓"
            elif j == i:
                cls = "step-active"; tick = "◌"
            else:
                cls = "step-wait";   tick = "·"
            html += f'<div class="pipeline-step {cls}"><span>{tick}</span><span>{icon} {label}</span></div>'
        step_box.markdown(html, unsafe_allow_html=True)
        st.session_state[keys[i]] = fn()
        time.sleep(0.05)

    # all done
    html = "".join(
        f'<div class="pipeline-step step-done"><span>✓</span><span>{icon} {label}</span></div>'
        for icon, label in STEPS
    )
    step_box.markdown(html, unsafe_allow_html=True)
    return st.session_state._s4


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ✦ SEO Writer")
    st.markdown('<p style="font-size:.8rem;color:#6b7280;margin-top:-.5rem;margin-bottom:1.5rem;">AI-powered article generation</p>', unsafe_allow_html=True)
    topic  = st.text_input("Topic", placeholder="e.g. best CRM tools for startups")
    length = st.number_input("Word count", min_value=300, max_value=5000, value=1000, step=100)
    generate = st.button("⚡  Generate Article")

    if "last_result" in st.session_state:
        st.markdown("---")
        data = st.session_state["last_result"]
        wc = g(data, "word_count", "—")
        st.markdown(f'<p style="font-size:.8rem;color:#9ca3af">Last run · <b style="color:#e5e7eb">{wc} words</b></p>', unsafe_allow_html=True)


# ── Main canvas ───────────────────────────────────────────────────────────────
st.markdown('<div class="main-canvas">', unsafe_allow_html=True)

if generate:
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        step_box = st.empty()
        try:
            result = run_pipeline(topic.strip(), int(length), step_box)
            st.session_state["last_result"] = result
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()
        time.sleep(0.4)
        step_box.empty()
        st.rerun()

if "last_result" in st.session_state:
    data = st.session_state["last_result"]

    title    = g(data, "title", "Untitled")
    intro    = g(data, "introduction", "")
    sections = g(data, "sections",  [])
    faq      = g(data, "faq",       [])
    conc     = g(data, "conclusion", "")
    meta     = g(data, "seo_metadata", {})
    internal = g(data, "internal_links_used", [])
    external = g(data, "external_links_used", [])
    wc       = g(data, "word_count", 0)

    # ── Article header ──
    st.markdown(f"""
    <span class="art-label">SEO Article</span>
    <h1 class="art-h1">{title}</h1>
    <div class="art-meta">
        <span>📄 {wc:,} words</span>
        <span>·</span>
        <span>⏱ ~{round(wc/200)} min read</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Intro ──
    if intro:
        st.markdown(f'<p class="art-intro">{intro}</p>', unsafe_allow_html=True)

    # ── SEO card ──
    if meta:
        m = meta if isinstance(meta, dict) else meta.__dict__
        sec_kws = m.get("secondary_keywords", [])
        pills = "".join(f'<span class="kw-pill">{k}</span>' for k in sec_kws)
        st.markdown(f"""
        <div class="seo-card">
            <div class="seo-card-title">🏷 SEO Metadata</div>
            <div class="seo-row"><span class="seo-key">Title tag</span><span class="seo-val">{m.get('title_tag','—')}</span></div>
            <div class="seo-row"><span class="seo-key">Meta description</span><span class="seo-val">{m.get('meta_description','—')}</span></div>
            <div class="seo-row"><span class="seo-key">Primary keyword</span><span class="seo-val"><code>{m.get('primary_keyword','—')}</code></span></div>
            <div class="seo-row"><span class="seo-key">Secondary keywords</span><span class="seo-val">{pills}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="art-divider">', unsafe_allow_html=True)

    # ── Sections ──
    for sec in sections:
        heading = g(sec, "heading", "")
        level   = g(sec, "level", "H2").upper()
        content = g(sec, "content", "")
        tag = "art-h2" if level == "H2" else "art-h3"
        st.markdown(f'<h2 class="{tag}">{heading}</h2>', unsafe_allow_html=True)
        # Split into paragraphs
        for para in content.split("\n\n"):
            para = para.strip()
            if para:
                st.markdown(f'<p class="art-p">{para}</p>', unsafe_allow_html=True)

    # ── Conclusion ──
    if conc:
        st.markdown(f"""
        <div class="art-conclusion">
            <div class="art-conclusion-label">✦ Conclusion</div>
            {conc}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="art-divider">', unsafe_allow_html=True)

    # ── FAQ ──
    if faq:
        st.markdown('<h2 class="art-h2">Frequently Asked Questions</h2>', unsafe_allow_html=True)
        st.markdown('<div class="faq-wrap">', unsafe_allow_html=True)
        for item in faq:
            q = g(item, "question", "")
            a = g(item, "answer", "")
            st.markdown(f"""
            <div class="faq-item">
                <div class="faq-q">{q}</div>
                <div class="faq-a">{a}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Links ──
    if internal or external:
        st.markdown('<hr class="art-divider">', unsafe_allow_html=True)
        st.markdown('<h2 class="art-h2">Links</h2>', unsafe_allow_html=True)
        if internal:
            st.markdown('<p style="font-size:.8rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#9ca3af;margin-bottom:.5rem">Internal</p>', unsafe_allow_html=True)
            st.markdown('<div class="links-grid">', unsafe_allow_html=True)
            for lnk in internal:
                st.markdown(f"""
                <div class="link-card">
                    <div class="anchor">↗ {lnk.get('anchor_text','')}</div>
                    <div class="hint">{lnk.get('suggested_topic','')}</div>
                    <span class="badge">{lnk.get('placed_in_section','')}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        if external:
            st.markdown('<p style="font-size:.8rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#9ca3af;margin:.8rem 0 .5rem">External</p>', unsafe_allow_html=True)
            st.markdown('<div class="links-grid">', unsafe_allow_html=True)
            for lnk in external:
                url = lnk.get('url','#')
                st.markdown(f"""
                <div class="link-card">
                    <div class="anchor"><a href="{url}" target="_blank" style="color:#6366f1;text-decoration:none">🌐 {lnk.get('anchor_text','')}</a></div>
                    <div class="hint">{url}</div>
                    <span class="badge">{lnk.get('placed_in_section','')}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Raw JSON ──
    st.markdown('<hr class="art-divider">', unsafe_allow_html=True)
    with st.expander("{ } Raw JSON"):
        try:
            raw = data.model_dump() if hasattr(data, "model_dump") else data
            st.json(raw)
        except Exception:
            st.write(data)

else:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">✦</div>
        <h3>No article yet</h3>
        <p>Enter a topic and word count in the sidebar<br>then hit <b>⚡ Generate Article</b></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)