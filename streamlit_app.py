import streamlit as st
import asyncio
import time

from app.src.services.serper import get_serper_responses
from app.src.services.scrapper import run_scraping_pipeline
from app.src.services.prelim import run_haiku_analysis
from app.src.services.consolidator import run_consolidator
from app.src.services.writer import run_writer

st.set_page_config(
    page_title="SEO Article Generator",
    page_icon="✍️",
    layout="wide",
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .section-card {
        background: #f8f9fa;
        border-left: 4px solid #4f8bf9;
        padding: 1rem 1.2rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    .faq-card {
        background: #fff8f0;
        border-left: 4px solid #f97316;
        padding: 0.8rem 1.2rem;
        border-radius: 6px;
        margin-bottom: 0.8rem;
    }
    .meta-pill {
        display: inline-block;
        background: #e0edff;
        color: #1d4ed8;
        border-radius: 999px;
        padding: 2px 12px;
        margin: 3px 3px 3px 0;
        font-size: 0.78rem;
        font-weight: 500;
    }
    .kv-row { display: flex; gap: 0.5rem; margin-bottom: 0.3rem; }
    .kv-label { font-weight: 600; min-width: 160px; color: #374151; }
    h1.article-title { font-size: 2rem; font-weight: 800; margin-bottom: 0.3rem; }
    .intro-text { font-size: 1.05rem; color: #374151; line-height: 1.7; }
    .conclusion-text { font-size: 1rem; color: #374151; line-height: 1.7;
                       background:#f0fdf4; border-left:4px solid #22c55e;
                       padding:1rem 1.2rem; border-radius:6px; }
    .link-row { font-size: 0.88rem; margin-bottom: 0.3rem; }
</style>
""", unsafe_allow_html=True)


def run_pipeline(topic: str, length: int, status_placeholder):
    steps = [
        ("🔍 Fetching search results…",    lambda: get_serper_responses(topic)),
        ("🕸️ Scraping source pages…",       lambda: run_scraping_pipeline(st.session_state._serper)),
        ("🤖 Analysing contents…",  lambda: asyncio.run(run_haiku_analysis(st.session_state._pages, topic))),
        ("📐 Building content blueprint…", lambda: asyncio.run(run_consolidator(st.session_state._analyses, topic, length))),
        ("✍️ Writing article…",             lambda: asyncio.run(run_writer(st.session_state._blueprint, length))),
    ]
    keys = ["_serper", "_pages", "_analyses", "_blueprint", "_written"]

    progress = status_placeholder.progress(0, text=steps[0][0])
    for i, (label, fn) in enumerate(steps):
        progress.progress(i / len(steps), text=label)
        result = fn()
        st.session_state[keys[i]] = result
        time.sleep(0.1)   # give Streamlit a tick to render

    progress.progress(1.0, text="✅ Done!")
    return st.session_state._written


def render_seo_metadata(meta: dict):
    st.markdown("#### 🏷️ SEO Metadata")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f'<div class="kv-row"><span class="kv-label">Title tag</span>{meta.get("title_tag","—")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kv-row"><span class="kv-label">Primary keyword</span><code>{meta.get("primary_keyword","—")}</code></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kv-row"><span class="kv-label">Meta description</span>{meta.get("meta_description","—")}</div>', unsafe_allow_html=True)
    sec = meta.get("secondary_keywords", [])
    if sec:
        pills = "".join(f'<span class="meta-pill">{k}</span>' for k in sec)
        st.markdown(f"**Secondary keywords:** {pills}", unsafe_allow_html=True)


def render_links(internal: list, external: list):
    with st.expander("🔗 Internal & External Links", expanded=False):
        if internal:
            st.markdown("**Internal links**")
            for lnk in internal:
                st.markdown(
                    f'<div class="link-row">📎 <b>{lnk.get("anchor_text")}</b> — '
                    f'{lnk.get("suggested_topic","")}'
                    f'<span style="color:#9ca3af"> [{lnk.get("placed_in_section","")}]</span></div>',
                    unsafe_allow_html=True,
                )
        if external:
            st.markdown("**External links**")
            for lnk in external:
                st.markdown(
                    f'<div class="link-row">🌐 <a href="{lnk.get("url","#")}" target="_blank">'
                    f'{lnk.get("anchor_text","link")}</a>'
                    f'<span style="color:#9ca3af"> [{lnk.get("placed_in_section","")}]</span></div>',
                    unsafe_allow_html=True,
                )


def render_article(data):
    """Main renderer — handles both Pydantic objects and plain dicts."""

    def g(obj, key, default=None):
        """Attribute-or-key getter."""
        if hasattr(obj, key):
            return getattr(obj, key, default)
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default

    title = g(data, "title", "Untitled")
    wc    = g(data, "word_count", "—")

    col_title, col_wc = st.columns([4, 1])
    with col_title:
        st.markdown(f'<h1 class="article-title">{title}</h1>', unsafe_allow_html=True)
    with col_wc:
        st.metric("Word count", f"{wc:,}" if isinstance(wc, int) else wc)

    st.divider()

    intro = g(data, "introduction")
    if intro:
        st.markdown("#### 📖 Introduction")
        st.markdown(f'<p class="intro-text">{intro}</p>', unsafe_allow_html=True)

    meta = g(data, "seo_metadata")
    if meta:
        st.divider()
        render_seo_metadata(meta if isinstance(meta, dict) else meta.__dict__)

    st.divider()

    sections = g(data, "sections", [])
    if sections:
        st.markdown("#### 📚 Article Sections")
        for sec in sections:
            heading = g(sec, "heading", "Section")
            level   = g(sec, "level", "H2")
            content = g(sec, "content", "")
            with st.expander(f"{level} · {heading}", expanded=True):
                st.markdown(
                    f'<div class="section-card">{content}</div>',
                    unsafe_allow_html=True,
                )

    faq = g(data, "faq", [])
    if faq:
        st.divider()
        st.markdown("#### ❓ FAQ")
        for item in faq:
            q = g(item, "question", "")
            a = g(item, "answer", "")
            st.markdown(
                f'<div class="faq-card"><b>Q: {q}</b><br/><br/>{a}</div>',
                unsafe_allow_html=True,
            )

    conclusion = g(data, "conclusion")
    if conclusion:
        st.divider()
        st.markdown("#### 🏁 Conclusion")
        st.markdown(f'<div class="conclusion-text">{conclusion}</div>', unsafe_allow_html=True)

    internal = g(data, "internal_links_used", [])
    external = g(data, "external_links_used", [])
    if internal or external:
        st.divider()
        render_links(internal, external)

    st.divider()
    with st.expander("🗂️ Raw JSON output", expanded=False):
        import json
        try:
            raw = data.model_dump() if hasattr(data, "model_dump") else data
            st.json(raw)
        except Exception:
            st.write(data)


with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/document--v1.png", width=64)
    st.title("SEO Article Generator")
    st.caption("Powered by your content pipeline")

    st.divider()
    topic  = st.text_input("Article topic", placeholder="e.g. best productivity tools for remote teams")
    length = st.number_input("Target word count", min_value=300, max_value=5000, value=1000, step=100)

    generate = st.button("⚡ Generate", type="primary", use_container_width=True)

    st.divider()
    st.caption("Pipeline steps")
    st.markdown("""
1. 🔍 Serper search  
2. 🕸️ Page scraping  
3. 🤖 Preliminary analysis  
4. 📐 Blueprint consolidation  
5. ✍️ Article writing  
    """)

st.markdown("## ✍️ Generated Article")

if generate:
    if not topic.strip():
        st.warning("Please enter an article topic in the sidebar.")
    else:
        status_box = st.empty()
        with st.spinner("Running pipeline…"):
            try:
                result = run_pipeline(topic.strip(), int(length), status_box)
                st.session_state["last_result"] = result
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.stop()

if "last_result" in st.session_state:
    render_article(st.session_state["last_result"])
else:
    st.info("Enter a topic and word count in the sidebar, then hit **⚡ Generate**.")