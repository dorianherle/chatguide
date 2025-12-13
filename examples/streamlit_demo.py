"""ChatGuide Streamlit App - Hotel Receptionist Demo."""

import streamlit as st
import os
from dotenv import load_dotenv
from src.chatguide import ChatGuide

load_dotenv()

# Page config
st.set_page_config(page_title="Hotel Reception", page_icon="🏨", layout="wide")


# ============================================================================
# SESSION STATE
# ============================================================================

if "chatguide" not in st.session_state:
    st.session_state.chatguide = None
    st.session_state.messages = []
    st.session_state.started = False


# ============================================================================
# BUSINESS LOGIC
# ============================================================================

def initialize_chatguide() -> ChatGuide:
    """Initialize ChatGuide instance."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
    cg = ChatGuide(api_key=api_key, debug=False)
    cg.load_config("realistic_hotel_config.yaml")
    return cg


def handle_tool_click(cg: ChatGuide, tool_id: str, option: str):
    """Handle tool button click."""
    st.session_state.messages.append({
        "role": "user",
        "content": option
    })
    
    # Update state and add message
    cg.state.set("purpose", option)
    cg.add_user_message(option)
    
    # Evaluate adjustments and track
    fired = cg.adjustments.evaluate(cg.state, cg.plan, cg.tone)
    
    # Get response
    reply = cg.chat()
    
    # Get any adjustments fired during chat
    all_fired = list(set(fired + cg.get_last_fired_adjustments()))
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply.assistant_reply,
        "tools": cg.get_pending_ui_tools(),
        "adjustments": all_fired
    })


def handle_chat_input(cg: ChatGuide, prompt: str):
    """Handle regular chat input."""
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    cg.add_user_message(prompt)
    reply = cg.chat()
    
    fired = cg.get_last_fired_adjustments()
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply.assistant_reply,
        "tools": cg.get_pending_ui_tools(),
        "adjustments": fired
    })


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_sidebar():
    """Render sidebar with controls and state monitor."""
    with st.sidebar:
        st.title("🏨 Hotel Reception")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start", use_container_width=True):
                st.session_state.chatguide = initialize_chatguide()
                st.session_state.started = True
                st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("Reset", use_container_width=True):
                st.session_state.chatguide = None
                st.session_state.started = False
                st.session_state.messages = []
                st.rerun()
        
        # State monitor
        if st.session_state.started and st.session_state.chatguide:
            render_state_monitor()


def render_state_monitor():
    """Render state monitoring panel."""
    st.divider()
    st.subheader("System Status")
    
    cg = st.session_state.chatguide
    
    # State
    st.write("**State:**")
    state_dict = cg.state.to_dict()
    changed_state = {k: v for k, v in state_dict.items() if v is not None and v != False and v != ""}
    if changed_state:
        for key, value in changed_state.items():
            st.text(f"  {key}: {value}")
    else:
        st.text("  (empty)")
    
    # Plan
    st.write("**Plan:**")
    plan_info = cg.plan.to_dict()
    st.text(f"  Block {plan_info['current_index']} / {len(plan_info['blocks'])}")
    current = cg.plan.get_current_block()
    if current:
        st.text(f"  Tasks: {', '.join(current)}")
    
    # Tone
    st.write("**Tone:**")
    if cg.tone:
        st.text(f"  {', '.join(cg.tone)}")
    else:
        st.text("  professional")
    
    # Adjustments
    st.write("**Adjustments:**")
    adj_data = cg.adjustments.to_dict()
    fired_count = sum(1 for a in adj_data['adjustments'] if a['fired'])
    total_count = len(adj_data['adjustments'])
    st.text(f"  {fired_count} / {total_count} fired")
    
    # Messages
    st.write("**Messages:**")
    st.text(f"  {len(st.session_state.messages)} total")


def render_chat_message(msg: dict):
    """Render a single chat message."""
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
    
    # Show fired adjustments
    if "adjustments" in msg and msg["adjustments"]:
        for adj_name in msg["adjustments"]:
            st.info(f"⚡ Adjustment fired: **{adj_name}**")
    
    if "tools" in msg and msg["tools"]:
        render_tools(msg)


def render_tools(msg: dict):
    """Render interactive tools."""
    for tool_idx, tool_data in enumerate(msg["tools"]):
        tool_id = tool_data.get("tool", "")
        tool_args = tool_data.get("args", {})
        
        if tool_id == "html.button_choice":
            options = tool_args.get("options", [])
            if not options:
                st.warning("Tool called with no options")
                continue
            
            cols = st.columns(len(options))
            
            for idx, option in enumerate(options):
                with cols[idx]:
                    msg_idx = st.session_state.messages.index(msg)
                    if st.button(option, key=f"tool_{msg_idx}_{tool_idx}_{idx}", use_container_width=True):
                        cg = st.session_state.chatguide
                        handle_tool_click(cg, tool_id, option)
                        st.rerun()
        
        elif tool_id == "html.card_swipe":
            st.components.v1.html("""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <style>
                .swipe-animation{
                  position:relative;
                  width: 500px;
                  height: 200px;
                  margin: 40px auto;
                  overflow:hidden;
                }
                .credit-card{
                  width: 250px;
                  height: 140px;
                  background:#dadada;
                  border-radius:10px;
                  position:relative;
                  z-index: 2;
                  animation: swipe-card 2s ease-in-out infinite;
                }
                .credit-card .card-stripe{
                  position:absolute;
                  background:#434343;
                  width: 100%;
                  height: 25px;
                  bottom:30px;
                }
                .swiper-top, .swiper-bottom{  
                  border-radius:8px 8px 0 0;
                  position:absolute;
                  background: #434343;  
                }
                .swiper-top{ 
                  height: 20px;
                  bottom:105px;
                  z-index: 0;
                  width: 400px;
                  left: calc(50% - 200px);
                }
                .swiper-bottom{
                  height: 100px;
                  bottom:0;
                  z-index: 3;
                  width: 420px;
                  left: calc(50% - 210px);
                }
                .light-indicator{
                  position:absolute;
                  top:10px;
                  right:15px;
                  width: 10px;
                  height: 10px;
                  border-radius:50%;
                  background:#dadada; 
                  animation: reader-light 2s ease-in-out infinite;
                }
                @keyframes swipe-card{
                  0%{
                    margin-left: -150px;
                    transform:rotate(25deg);
                  }
                  50%{
                    transform:rotate(0deg);
                  }
                  100%{
                    margin-left: 500px;
                    transform:rotate(-25deg);
                  }
                }
                @keyframes reader-light{
                  0%{
                    background:#dadada; 
                  }
                  60%{
                    background:#B8FD99; 
                  }
                }
                </style>
                <div class="swipe-animation">
                  <div class="credit-card">
                    <div class="card-stripe"></div>
                  </div>
                  <div class="swiper-top"></div>
                  <div class="swiper-bottom">
                    <div class="light-indicator"></div>
                  </div>
                </div>
            </div>
            """, height=350)


# ============================================================================
# MAIN APP
# ============================================================================

render_sidebar()

st.title("🏨 Grand Plaza Hotel")
st.caption("Professional Reception System")

# Welcome state
if not st.session_state.started:
    st.info("👈 Click 'Start' in the sidebar to begin")

# Initial greeting
elif len(st.session_state.messages) == 0:
    cg = st.session_state.chatguide
    
    # Get first AI response
    reply = cg.chat()
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply.assistant_reply,
        "tools": cg.get_pending_ui_tools()
    })
    
    st.rerun()

# Active conversation
else:
    for msg in st.session_state.messages:
        render_chat_message(msg)
    
    if prompt := st.chat_input("Type your message..."):
        handle_chat_input(st.session_state.chatguide, prompt)
        st.rerun()

