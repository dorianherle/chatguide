import streamlit as st
from chat_service import ChatService
import json
from datetime import datetime


def start_chat(language="en"):
    st.session_state.chat_service = ChatService(debug=True)
    st.session_state.chat_service.initialize_guide(language)
    st.session_state.messages = []
    st.session_state.prompt_log = []  # Log all prompts and replies
    
    # Generate first message from the model in the selected language
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    first_reply = st.session_state.chat_service.guide.chat(
        model="gemini/gemini-2.5-flash-lite",
        api_key=api_key
    )
    starting_msg = first_reply.assistant_reply
    st.session_state.messages.append({
        "role": "assistant", 
        "content": starting_msg
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
            
            # Print clean debug info to console
            debug_info = st.session_state.chat_service.get_debug_info()
            user_name = st.session_state.chat_service.guide.user_name
            
            # Get state description
            state_descriptions = {
                0: "Getting name & origin",
                1: "Language & location", 
                2: "Reflection & suggestions"
            }
            current_state_desc = state_descriptions.get(debug_info['state'], f"State {debug_info['state']}")
            total_states = len(st.session_state.chat_service.guide.state_machine.states)
            
            print(f"\nTURN {debug_info['turn_count']} │ PHASE: {current_state_desc} ({debug_info['state']+1}/{total_states}) │ {'✅ CONVERSATION COMPLETE' if debug_info['is_finished'] else '⏳ IN PROGRESS'}")
            
            # User input with actual name
            user_msg = prompt if len(prompt) <= 60 else prompt[:57] + "..."
            print(f"👤 {user_name}: {user_msg}")
            
            # Tasks status
            current = debug_info['current_tasks']
            if current:
                print(f"📋 CURRENT: {', '.join(current)}")
            else:
                print(f"📋 CURRENT: (none - batch complete)")

            # Task results from this turn
            completed_tasks = [f"{t.task_id}='{t.result}'" for t in reply.tasks if t.result]
            if completed_tasks:
                print(f"✅ COMPLETED: {', '.join(completed_tasks)}")

            # Persistent task results
            persistent_results = [f"{t.task_id}='{t.result}'" for t in reply.persistent_tasks if t.result]
            if persistent_results:
                print(f"🔄 PERSISTENT: {', '.join(persistent_results)}")

            # Failed tasks
            failed_tasks = [t for t in debug_info['current_tasks'] if debug_info['task_status'].get(t) == "failed"]
            if failed_tasks:
                print(f"💀 FAILED: {', '.join(failed_tasks)}")
            
            # Known information
            if debug_info['task_results']:
                info_items = [f"{k}={v}" for k, v in debug_info['task_results'].items() if v and k not in ['detect_info_updates']]
                if info_items:
                    # Truncate memory line if too long
                    memory_line = ', '.join(info_items[:5])
                    if len(memory_line) > 60:
                        memory_line = memory_line[:57] + "..."
                    print(f"💾 MEMORY: {memory_line}")
            
            # Bot reply - FULL TEXT
            print("🤖 Sol:")
            print(reply.assistant_reply)
            
            print("\n📄 FULL PROMPT:")
            print(outgoing_prompt)
            print()
                
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

