import streamlit as st
from chat_service import ChatService
import json
from datetime import datetime


def start_chat(language="en"):
    st.session_state.chat_service = ChatService(debug=True)
    st.session_state.chat_service.initialize_guide(language)
    st.session_state.messages = []
    st.session_state.prompt_log = []
    
    # Generate first message using the "introduce_yourself" task
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    first_reply = st.session_state.chat_service.guide.chat(
        model="gemini/gemini-2.5-flash-lite",
        api_key=api_key
    )
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": first_reply.assistant_reply
    })

def download_chat_data():
    """Generate and download comprehensive chat data"""
    if "messages" not in st.session_state or not st.session_state.messages:
        return None
    
    # Get debug info
    debug_info = st.session_state.chat_service.get_debug_info()
    
    # Compile chat data - include ALL messages and logs
    chat_data = {
        "export_timestamp": datetime.now().isoformat(),
        "chat_messages": st.session_state.messages,  # All chat messages
        "prompt_log": st.session_state.get("prompt_log", []),  # Detailed logs
        "final_debug_info": debug_info  # Final state
    }
    
    # Convert to JSON string
    json_data = json.dumps(chat_data, indent=2, ensure_ascii=False)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chatguide_v2_export_{timestamp}.json"
    
    return json_data.encode('utf-8'), filename

    

def main():
    # Password protection
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Access Required")
        st.markdown("Please enter the passcode to access the ChatGuide Demo V2")
        
        passcode = st.text_input("Passcode:", type="password")
        if st.button("Submit"):
            if passcode == "112233":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid passcode")
        return
    
    st.title("Belonging Demo V2 🚀")
    st.markdown("**NEW:** Explicit state machine + output validation")
    
    # Language selector before starting chat
    if "chat_service" not in st.session_state or st.session_state.chat_service is None:
        st.markdown("### Choose your language / Choisissez votre langue")
        language_options = {
            "English": "en",
            "Español": "es",
            "Français": "fr",
            "Deutsch": "de",
            "Italiano": "it",
            "Português": "pt",
            "中文": "zh",
            "日本語": "ja",
            "한국어": "ko"
        }
        selected_language = st.selectbox("Language:", list(language_options.keys()))
        if st.button("Start Chat / Commencer"):
            start_chat(language_options[selected_language])
            st.rerun()
        return

    # Top-level controls on main page
    def logout():
        st.session_state.authenticated = False
        st.session_state.messages = []
        st.session_state.chat_service = None
        st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("🔄 Reset Chat", on_click=start_chat)
    with col2:
        download_data = download_chat_data()
        if download_data:
            json_bytes, filename = download_data
            st.download_button(
                "📥 Download Chat Data",
                data=json_bytes,
                file_name=filename,
                mime="application/json",
                help="Download prompts and replies log"
            )
        else:
            st.button("📥 Download Chat Data", disabled=True, help="No chat data to download")
    with col3:
        st.button("🚪 Logout", on_click=logout)
    
    # Sidebar: What Sol knows about you
    with st.sidebar:
        st.header("🧠 What Sol knows about you")
        
        debug_info = st.session_state.chat_service.get_debug_info()
        task_results = debug_info['tracker']['results']
        
        if task_results:
            # Filter out system tasks
            user_info = {k: v for k, v in task_results.items() if k not in ['detect_info_updates'] and v}
            
            if user_info:
                # Group by category
                basic_info = {}
                moving_info = {}
                language_info = {}
                social_info = {}
                emotional_info = {}
                goals_info = {}
                
                for key, value in user_info.items():
                    if key in ['get_name', 'get_age', 'get_origin', 'get_location']:
                        basic_info[key.replace('get_', '').replace('_', ' ').title()] = value
                    elif key in ['get_move_date', 'get_move_reason', 'get_move_choice']:
                        moving_info[key.replace('get_', '').replace('_', ' ').title()] = value
                    elif key in ['get_language_level', 'get_language_comfort']:
                        language_info[key.replace('get_', '').replace('_', ' ').title()] = value
                    elif key in ['get_social_network', 'get_family_location', 'get_friends_origin']:
                        social_info[key.replace('get_', '').replace('_', ' ').title()] = value
                    elif key in ['get_emotion', 'get_homesickness', 'get_grief_intensity', 'get_adaptation_level']:
                        emotional_info[key.replace('get_', '').replace('_', ' ').title()] = value
                    elif key in ['get_biggest_challenge', 'get_support_system', 'get_stay_duration', 'get_primary_goal']:
                        goals_info[key.replace('get_', '').replace('_', ' ').title()] = value
                
                if basic_info:
                    st.subheader("👤 Basic Info")
                    for k, v in basic_info.items():
                        st.write(f"**{k}:** {v}")
                
                if moving_info:
                    st.subheader("✈️ Moving Details")
                    for k, v in moving_info.items():
                        st.write(f"**{k}:** {v}")
                
                if language_info:
                    st.subheader("🗣️ Language")
                    for k, v in language_info.items():
                        st.write(f"**{k}:** {v}")
                
                if social_info:
                    st.subheader("👥 Social Connections")
                    for k, v in social_info.items():
                        st.write(f"**{k}:** {v}")
                
                if emotional_info:
                    st.subheader("💭 Emotional State")
                    for k, v in emotional_info.items():
                        st.write(f"**{k}:** {v}")
                
                if goals_info:
                    st.subheader("🎯 Goals & Support")
                    for k, v in goals_info.items():
                        st.write(f"**{k}:** {v}")
            else:
                st.info("Sol is getting to know you... 🤗")
        else:
            st.info("Sol is getting to know you... 🤗")
        
        st.divider()
        st.caption(f"Turn: {debug_info['interaction']['turn_count']} | Phase: {debug_info['flow']['current_index'] + 1}")
    
    # Visual divider between controls and chat
    st.divider()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        try:
            with st.spinner("Thinking..."):
                # Send message and capture the exact prompt used by the model
                reply, outgoing_prompt = st.session_state.chat_service.send_message(prompt)
                
                # Log the interaction
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user_input": prompt,
                    "outgoing_prompt": outgoing_prompt,
                    "ai_reply": reply.assistant_reply,
                    "task_results": [{"task_id": t.task_id, "result": t.result} for t in reply.tasks]
                }
                st.session_state.prompt_log.append(log_entry)
            
            # Add assistant response
            st.session_state.messages.append({
                "role": "assistant", 
                "content": reply.assistant_reply
            })
            
            with st.chat_message("assistant"):
                st.write(reply.assistant_reply)
            
            # Beautiful debug output to console
            import sys
            from src.chatguide import ChatGuide
            
            # Force flush to ensure output appears
            print("\n" + "="*70, file=sys.stderr, flush=True)
            print("DEBUG OUTPUT", file=sys.stderr, flush=True)
            print("="*70, file=sys.stderr, flush=True)
            
            # Compact one-liner
            compact = st.session_state.chat_service.guide.print_debug_compact()
            print(f"\n{compact}", file=sys.stderr, flush=True)
            
            # Beautiful formatted response
            formatted = ChatGuide.print_response(reply)
            print(formatted, file=sys.stderr, flush=True)
            
            # Full state debug
            full_debug = st.session_state.chat_service.guide.print_debug()
            print(full_debug, file=sys.stderr, flush=True)
            
            # Full prompt
            print("\n" + "=" * 70, file=sys.stderr, flush=True)
            print("FULL PROMPT:", file=sys.stderr, flush=True)
            print("-" * 70, file=sys.stderr, flush=True)
            print(outgoing_prompt, file=sys.stderr, flush=True)
            print("=" * 70 + "\n", file=sys.stderr, flush=True)
            
            # Rerun to update sidebar with fresh state
            st.rerun()
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Sorry, I encountered an error. Please try again."
            })

if __name__ == "__main__":
    main()

