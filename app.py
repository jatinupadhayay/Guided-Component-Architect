import streamlit as st
import streamlit.components.v1 as components
import json
from main import orchestrate_agentic_loop

def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

st.set_page_config(
    page_title="Guided Component Architect",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0.75rem 1.25rem !important; max-width: 100% !important; }

/* Top navbar */
.navbar {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 12px;
}
.navbar-brand { display: flex; align-items: center; gap: 8px; }
.navbar-logo {
  width: 28px; height: 28px; background: #6366f1; border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 15px; font-weight: 700;
}
.navbar-title { font-size: 15px; font-weight: 600; color: #111; }
.navbar-sub   { font-size: 11px; color: #9ca3af; }

/* Panel headers */
.pane-title {
  font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #9ca3af;
  padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; margin-bottom: 10px;
  display: flex; align-items: center; gap: 6px;
}
.pane-dot { width: 6px; height: 6px; border-radius: 50%; background: #6366f1; display: inline-block; }

/* Chat bubbles */
.bubble-user {
  background: #6366f1; color: #fff;
  border-radius: 18px 18px 4px 18px;
  padding: 9px 14px; font-size: 14px;
  max-width: 84%; word-break: break-word; margin: 5px 0;
}
.bubble-bot {
  background: #f3f4f6; color: #374151;
  border-radius: 18px 18px 18px 4px;
  padding: 9px 14px; font-size: 13px; line-height: 1.6;
  max-width: 96%; word-break: break-word; margin: 3px 0;
}
.step-success { color: #16a34a; }
.step-error   { color: #dc2626; }
.step-warn    { color: #d97706; }
.step-info    { color: #4f46e5; }

/* Thinking dots */
@keyframes blink { 0%,80%,100%{opacity:0} 40%{opacity:1} }
.dot { display:inline-block; width:6px; height:6px; border-radius:50%;
       background:#6366f1; margin:0 2px; animation: blink 1.4s infinite; }
.dot:nth-child(2){animation-delay:.2s} .dot:nth-child(3){animation-delay:.4s}

/* Preview chrome */
.preview-chrome {
  background:#f9fafb; border:1px solid #e5e7eb; border-radius:10px 10px 0 0;
  padding:8px 14px; display:flex; align-items:center; gap:6px;
}
.cdot { width:10px; height:10px; border-radius:50%; }
.url-bar { background:#e5e7eb; border-radius:5px; padding:3px 10px;
           font-size:11px; color:#9ca3af; flex:1; margin-left:8px; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }

/* Make form input look clean */
textarea { border-radius: 10px !important; }

/* Expander clean look */
[data-testid="stExpander"] { border: 1px solid #e5e7eb !important; border-radius: 10px !important; }

/* Custom Chat Scroll for older Streamlit versions */
.chat-scroll {
    max-height: 450px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #f3f4f6;
    border-radius: 12px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ─── Settings / API Key Logic ─────────────────────────────
import os as _os
from dotenv import load_dotenv as _load
_load()

# Check .env keys
env_keys = {
    "groq":    _os.getenv("GROQ_API_KEY", ""),
    "openai":  _os.getenv("OPENAI_API_KEY", ""),
    "claude":  _os.getenv("ANTHROPIC_API_KEY", ""),
    "gemini":  _os.getenv("GOOGLE_API_KEY", ""),
}

# ─── Main Navbar ───────────────────────────────────────────
st.markdown("""
<div class="navbar">
  <div class="navbar-brand">
    <div class="navbar-logo">⚡</div>
    <div>
      <div class="navbar-title">Guided Component Architect</div>
      <div class="navbar-sub">Agentic &bull; Angular &bull; Design-System Governed</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Preparation & Run Logic ──────────────────────────────
user_input = None
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

def run_generation(prompt, model, retries, keys):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.history.append(prompt)
    
    logs = []
    final_data = None
    model_label = {
        "groq": "Groq Llama 3.3", "openai": "GPT-4o",
        "claude": "Claude 3.5", "gemini": "Gemini 2.0 Flash",
    }.get(model, model)

    with st.spinner(f"⚡ Generating with {model_label}..."):
        from main import orchestrate_agentic_loop
        for update in orchestrate_agentic_loop(
            prompt,
            max_retries=retries,
            model_preference=model,
            conversation_history=st.session_state.history[:-1],
            api_keys=keys,
        ):
            s, v = update["step"], update["value"]
            if s == "attempt": logs.append({"role":"assistant","content":f"🔄 <b>Attempt {v}</b>"})
            elif s == "generating": logs.append({"role":"assistant","content":f"⏳ {v}"})
            elif s == "validating": logs.append({"role":"assistant","content":f"🔍 {v}"})
            elif s == "failed":
                logs.append({"role":"assistant","content":f"❌ {v}"})
                for e in update.get("errors",[]):
                    logs.append({"role":"assistant","content":f"&nbsp;&nbsp;• {e}"})
            elif s == "correcting": logs.append({"role":"assistant","content":f"🧠 {v}"})
            elif s == "success":
                logs.append({"role":"assistant","content":"✅ Component validated & ready!"})
                final_data = update["data"]
            elif s == "max_retries":
                logs.append({"role":"assistant","content":f"⚠️ {v}"})
                final_data = update.get("data")

    st.session_state.messages.extend(logs)
    if final_data:
        st.session_state.final_code = final_data
    safe_rerun()

# ─── Main Split Layout ─────────────────────────────────────
left, right = st.columns([1, 1.6], gap="large")

# LEFT — Chat & Controls
with left:
    st.markdown('<div class="pane-title"><span class="pane-dot"></span>Configuration & Chat</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        model_choice = st.selectbox(
            "Select Model", options=["gemini", "groq", "openai", "claude"],
            format_func=lambda x: {
                "gemini": "💎 Gemini 2.0 Flash (Free)", "groq": "🦙 Groq Llama 3.3 (Free)",
                "openai": "🤖 OpenAI GPT-4o", "claude": "🟠 Claude 3.5 Sonnet",
            }[x], index=0, label_visibility="collapsed"
        )
    with c2:
        max_retries = st.number_input("Retries", 1, 5, 3, label_visibility="collapsed")

    ui_keys = {}
    if not env_keys.get(model_choice):
        st.warning(f"No API key for {model_choice} in .env")
        placeholder = {"openai": "sk-...", "groq": "gsk_...", "claude": "sk-ant-...", "gemini": "AIza..."}.get(model_choice, "Enter key...")
        ui_keys[model_choice] = st.text_input(f"{model_choice.capitalize()} API Key", type="password", placeholder=placeholder)
    else:
        st.caption(f"✅ Using {model_choice.upper()} key from .env")

    api_keys = {k: v for k, v in env_keys.items() if v}
    api_keys.update({k: v for k, v in ui_keys.items() if v})

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    chat_html = ""
    if not st.session_state.messages:
        chat_html = '<div style="text-align:center;padding:100px 10px;color:#d1d5db;"><div style="font-size:32px">💬</div><div style="font-size:14px;color:#9ca3af;margin-top:8px;">Describe an Angular component below</div></div>'
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                chat_html += f'<div style="display:flex;justify-content:flex-end"><div class="bubble-user">{msg["content"]}</div></div>'
            else:
                chat_html += f'<div class="bubble-bot">{msg["content"]}</div>'
    
    st.markdown(f'<div class="chat-scroll">{chat_html}</div>', unsafe_allow_html=True)

    with st.form("prompt_form", clear_on_submit=True):
        u_input = st.text_area("prompt", label_visibility="collapsed", placeholder='Describe your component...', height=72)
        bc1, bc2 = st.columns([4, 1])
        with bc1: submitted = st.form_submit_button("⚡ Generate", use_container_width=True, type="primary")
        with bc2: clear = st.form_submit_button("🗑️", use_container_width=True)
        
        if clear:
            st.session_state.messages = []
            st.session_state.final_code = None
            st.session_state.history = []
            safe_rerun()
        
        if submitted and u_input.strip():
            user_input = u_input.strip()

# RIGHT — Preview
with right:
    st.markdown('<div class="pane-title"><span class="pane-dot"></span>Live Preview</div>', unsafe_allow_html=True)
    if st.session_state.final_code:
        _c = st.session_state.final_code
        html_doc = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{margin:0;font-family:'Inter',sans-serif;background:linear-gradient(135deg,#6366f1,#a855f7);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box;}}{_c.get('css','')}</style><script>window.onload = () => {{document.body.innerHTML = document.body.innerHTML.replace(/\\\\{{\\\\s*([^\\\\}}]+)\\\\s*\\\\}}/g, (match, p1) => {{return '<span style="color:#6366f1;font-weight:600">[' + p1.trim() + ']</span>';}});}};</script></head><body>{_c.get('html','')}</body></html>"""
        st.markdown('<div class="preview-chrome"><div class="cdot" style="background:#ff5f57"></div><div class="cdot" style="background:#febc2e"></div><div class="cdot" style="background:#28c840"></div><div class="url-bar">localhost:4200/component-preview</div></div>', unsafe_allow_html=True)
        components.html(html_doc, height=400, scrolling=True)
        st.divider()
        th, tc, tt = st.tabs(["📄 HTML", "🎨 CSS", "⚙️ TypeScript"])
        with th: st.code(_c.get("html",""), language="html")
        with tc: st.code(_c.get("css","") or "/* Tailwind only */", language="css")
        with tt: st.code(_c.get("typescript",""), language="typescript")
        ex1, ex2, ex3 = st.columns(3)
        with ex1: st.download_button("⬇ HTML", _c.get("html",""), "component.html", "text/html", use_container_width=True)
        with ex2: st.download_button("⬇ CSS", _c.get("css",""), "component.css", "text/css", use_container_width=True)
        with ex3: st.download_button("⬇ TS", _c.get("typescript",""), "component.ts", "text/plain", use_container_width=True)
    else:
        st.markdown('<div style="border:1.5px dashed #e5e7eb;border-radius:14px;height:400px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#d1d5db;text-align:center;gap:8px;"><div style="font-size:40px">⚡</div><div style="font-size:15px;font-weight:600;color:#9ca3af">Preview appears here</div><div style="font-size:12px">Describe a component on the left →</div></div>', unsafe_allow_html=True)

# Final step: If user triggered generation, run it
if user_input:
    run_generation(user_input, model_choice, max_retries, api_keys)

