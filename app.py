import streamlit as st
from groq import Groq
import plotly.graph_objects as go
import plotly.express as px
import json

# --- 1. INITIALIZATION & UI ARCHITECTURE ---
st.set_page_config(page_title="SYNTHESIS ELITE", layout="wide")

# Global initialization to prevent AttributeErrors
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "history" not in st.session_state:
    st.session_state.history = []
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@200;300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp { background-color: #000000; color: #F5F5F7; font-family: 'Oswald', sans-serif; }
    h1 { font-family: 'Oswald', sans-serif; font-weight: 700; text-transform: uppercase; font-size: 3rem !important; margin-bottom: 0px; }
    h4 { font-family: 'Oswald', sans-serif; font-weight: 400; color: #8E8E93; letter-spacing: 2px; text-transform: uppercase; font-size: 0.75rem; margin-top: 20px; }
    
    /* Interactive Blocks */
    div.stButton > button {
        background: rgba(255, 255, 255, 0.03) !important; color: #00D4FF !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important; border-radius: 4px !important;
        font-family: 'Oswald', sans-serif; text-align: left !important; width: 100%; transition: 0.3s;
    }
    div.stButton > button:hover { 
        background: rgba(0, 212, 255, 0.1) !important; 
        border-color: #00D4FF !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
    }

    /* Tactical Chat Style: Tightened Layout */
    .custom-chat-message { 
        display: block; 
        padding: 12px 20px; 
        margin-bottom: 8px; 
        border-radius: 12px; 
        font-family: 'Oswald', sans-serif !important; 
        font-size: 1rem; 
        line-height: 1.3 !important; /* Fixed line gap */
        width: 100%; 
        white-space: pre-wrap; 
    }
    .custom-chat-message p { margin-bottom: 4px !important; margin-top: 0px !important; }
    
    .assistant-message { 
        background: linear-gradient(135deg, rgba(30, 20, 60, 0.9), rgba(80, 20, 180, 0.2)); 
        border-left: 4px solid #5014B4; color: #D1D1D1;
    }
    .user-message { 
        background: linear-gradient(135deg, rgba(16, 12, 41, 0.9), rgba(0, 212, 255, 0.2)); 
        border-left: 4px solid #00D4FF; color: #FFFFFF;
    }

    /* Input Styling */
    .stTextInput > div > div > input { font-family: 'Oswald', sans-serif; background-color: transparent !important; color: #FFFFFF !important; border-bottom: 1px solid #333 !important; font-size: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE LOGIC ---
class SynthesisEngine:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    def analyze(self, query):
        prompt = f"Analyze '{query}'. Return ONLY JSON. Schema: {{'map_focus':['Country'],'sentiment':{{'pos':int,'neu':int,'crit':int}},'entities':[{{'name':'str','link':'url'}}],'keywords':{{'labels':['str'],'values':[int]}},'points':['str'],'feed':[{{'title':'str','desc':'str'}}]}}"
        try:
            resp = self.client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=self.model, response_format={"type":"json_object"})
            return json.loads(resp.choices[0].message.content)
        except: return None

    def investigate(self, history, topic_context):
        try:
            # Determine the target based on history or context
            target = history[-1]['content'] if history else topic_context
            sys_prompt = f"Technical briefing on: {target}. Start directly with the analysis."
            
            # FIXED: Use .completions instead of .get_completions and add error checking
            resp = self.client.chat.completions.create(
                messages=[{"role": "system", "content": sys_prompt}] + history, 
                model=self.model
            )
            
            if hasattr(resp, 'choices') and len(resp.choices) > 0:
                return resp.choices[0].message.content
            return "ANALYSIS_UNAVAILABLE"
            
        except Exception as e:
            # Log the exact error to your console for easier debugging
            print(f"CRITICAL ENGINE ERROR: {e}") 
            return "INTEL_LINK_FAILED"
def trigger_search(matter, context_data=None):
    # Combine the matter with specific data for a more accurate deep-dive
    search_query = f"Deep-dive: {matter}"
    if context_data:
        search_query += f" based on this data: {context_data}"
        
    st.session_state.chat_log.append({"role": "user", "content": search_query})
    engine = SynthesisEngine(st.secrets["GROQ_API_KEY"])
    reply = engine.investigate(st.session_state.chat_log, st.session_state.get('last_q', 'General'))
    st.session_state.chat_log.append({"role": "assistant", "content": reply})

def reload_history(q):
    st.session_state.last_q = q
    engine = SynthesisEngine(st.secrets["GROQ_API_KEY"])
    st.session_state.analysis_data = engine.analyze(q)

# --- 4. DASHBOARD UI ---
with st.sidebar:
    st.markdown("#### 🕒 HISTORY")
    for h in st.session_state.history:
        st.button(f"🔎 {h}", key=f"h_{h}", on_click=reload_history, args=(h,))

st.title("SYNTHESIS ELITE🔍⚙️")
query = st.text_input("", placeholder="STRATEGIC FOCUS...", key="main_search")

if query and query != st.session_state.get('last_q'):
    engine = SynthesisEngine(st.secrets["GROQ_API_KEY"])
    if data := engine.analyze(query):
        st.session_state.analysis_data = data
        st.session_state.last_q = query
        if query not in st.session_state.history: st.session_state.history.insert(0, query)
        st.rerun()

if d := st.session_state.analysis_data:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("#### 🌍 TREND MAP")
        fig = px.choropleth(locations=d.get('map_focus', []), locationmode='country names', color_discrete_sequence=['#00D4FF'])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=150, margin=dict(l=0,r=0,b=0,t=0), geo=dict(bgcolor='rgba(0,0,0,0)', showframe=False))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### 📊 SENTIMENT PULSE")
        # Use .get() to prevent KeyError if 'pos', 'neu', or 'crit' are missing
        s = d.get('sentiment', {})
        pos = s.get('pos', 0)
        neu = s.get('neu', 0)
        crit = s.get('crit', 0)
        
        fig_p = go.Figure(go.Pie(
            labels=['Positive', 'Neutral', 'Critical'], 
            values=[pos, neu, crit], 
            hole=.7, 
            marker_colors=['#00D4FF', '#5014B4', '#FF3B30']
        ))
        fig_p.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=150, margin=dict(l=0,r=0,b=0,t=0), showlegend=False)
        st.plotly_chart(fig_p, use_container_width=True)
        
        # Ensures the analysis button also uses the safe retrieved values
        st.button("ANALYZE PULSE", on_click=trigger_search, 
                  args=(f"Sentiment drivers for {query}", f"Data: {pos}% Pos, {neu}% Neu, {crit}% Crit"))

    with c3:
        st.markdown("#### 🔗 ENTITY LINKAGES")
        for ent in d.get('entities', [])[:3]:
            ca, cb = st.columns([0.15, 0.85])
            ca.markdown(f"[🔗]({ent.get('link', '#')})")
            cb.button(ent['name'], key=f"e_{ent['name']}", on_click=trigger_search, args=(ent['name'],))

    with c4: # FIXED KEYWORD FLOW
        st.markdown("#### 📈 KEYWORD FLOW")
        k = d.get('keywords', {'labels': [], 'values': []})
        if k['labels'] and len(k['labels']) == len(k['values']):
            fig_k = px.bar(x=k['values'], y=k['labels'], orientation='h', color_discrete_sequence=['#00D4FF'])
            fig_k.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=150, margin=dict(l=0,r=0,b=0,t=0), xaxis_visible=False, yaxis_title=None)
            st.plotly_chart(fig_k, use_container_width=True)
        
        # Passes active keywords to the chat
        st.button("ANALYZE FLOW", on_click=trigger_search, 
                  args=(f"Keyword relationships for {query}", f"Active keywords: {', '.join(k['labels'])}"))

    st.divider()
    st.markdown("#### EXECUTIVE HIGHLIGHTS")
    h_cols = st.columns(4)
    points = d.get('points', [])
    
    # Use enumerate to create a unique index 'i' for every button key
    for i, (col, txt) in enumerate(zip(h_cols, points)):
        # Adding {i} ensures each key is unique even if the text 'txt' is similar
        col.button(str(txt), key=f"high_btn_{i}_{txt[:10]}", on_click=trigger_search, args=(txt,))
    st.markdown("#### DETAILED INTELLIGENCE BRIEFING")
    # Feed logic ensures specific interactive briefs for every data point
    for i, item in enumerate(d.get('feed', [])):
        # Display the source/title in the tactical cyan color
        st.markdown(f"<div style='color:#00D4FF; font-size:0.7rem;'>{item.get('title', 'INTEL').upper()}</div>", unsafe_allow_html=True)
        
        # Use unique index-based keys to prevent StreamlitDuplicateElementKey errors
        st.button(
            item.get('desc', 'No description available'), 
            key=f"feed_btn_{i}_{item.get('title', 'idx')[:5]}", 
            on_click=trigger_search, 
            args=(item.get('desc', ''),)
        )
# --- 5. TACTICAL CHAT ---
st.divider()
st.markdown("### 💬 Tactical Chat Investigation")
with st.container(height=450):
    for m in st.session_state.chat_log:
        r_cls = "user-message" if m["role"] == "user" else "assistant-message"
        st.markdown(f'<div class="custom-chat-message {r_cls}">{m["content"]}</div>', unsafe_allow_html=True)

if inp := st.chat_input("Request briefing..."):
    st.session_state.chat_log.append({"role": "user", "content": inp})
    engine = SynthesisEngine(st.secrets["GROQ_API_KEY"])
    ans = engine.investigate(st.session_state.chat_log, query if query else "General")
    st.session_state.chat_log.append({"role": "assistant", "content": ans})
    st.rerun()