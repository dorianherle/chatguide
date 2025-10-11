import streamlit as st
from chat_service_v2 import ChatServiceV2
import json
from datetime import datetime


def start_chat():
    st.session_state.chat_service = ChatServiceV2()
    st.session_state.messages = []
    st.session_state.prompt_log = []  # Log all prompts and replies
    starting_msg = st.session_state.chat_service.get_starting_message()
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
    
    if "chat_service" not in st.session_state or st.session_state.chat_service is None:
        start_chat()

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
            
            print("\n" + "┏" + "━"*78 + "┓")
            print(f"┃ 🔄 TURN {debug_info['turn_count']} │ STATE {debug_info['state']}/{len(st.session_state.chat_service.guide.state_machine.states)-1} │ {'✅ FINISHED' if debug_info['is_finished'] else '⏳ IN PROGRESS'}")
            print("┣" + "━"*78 + "┫")
            
            # User input with actual name
            user_msg = prompt if len(prompt) <= 60 else prompt[:57] + "..."
            print(f"┃ 👤 {user_name}: {user_msg}")
            print("┣" + "━"*78 + "┫")
            
            # Tasks status
            current = debug_info['current_tasks']
            if current:
                print(f"┃ 📋 CURRENT: {', '.join(current)}")
            else:
                print(f"┃ 📋 CURRENT: (none - batch complete)")
            
            # Task results from this turn
            completed_tasks = [f"{t.task_id}='{t.result}'" for t in reply.tasks if t.result]
            if completed_tasks:
                print(f"┃ ✅ COMPLETED: {', '.join(completed_tasks)}")
            
            # Persistent task results
            persistent_results = [f"{t.task_id}='{t.result}'" for t in reply.persistent_tasks if t.result]
            if persistent_results:
                print(f"┃ 🔄 PERSISTENT: {', '.join(persistent_results)}")
            
            print("┣" + "━"*78 + "┫")
            
            # Known information
            if debug_info['task_results']:
                info_items = [f"{k}={v}" for k, v in debug_info['task_results'].items() if v and k not in ['detect_info_updates']]
                if info_items:
                    # Truncate memory line if too long
                    memory_line = ', '.join(info_items[:5])
                    if len(memory_line) > 60:
                        memory_line = memory_line[:57] + "..."
                    print(f"┃ 💾 MEMORY: {memory_line}")
            
            print("┣" + "━"*78 + "┫")
            
            # Bot reply - FULL TEXT
            print("┃ 🤖 Sol:")
            for line in reply.assistant_reply.split('\n'):
                # Wrap long lines at 72 chars
                while len(line) > 72:
                    print(f"┃   {line[:72]}")
                    line = line[72:]
                if line:  # Print remaining part if any
                    print(f"┃   {line}")
            
            print("┣" + "━"*78 + "┫")
            print("┃ 📄 FULL PROMPT:")
            print("┣" + "━"*78 + "┫")
            for line in outgoing_prompt.split('\n'):
                # Wrap long lines at 74 chars
                while len(line) > 74:
                    print(f"┃ {line[:74]}")
                    line = line[74:]
                print(f"┃ {line}")
            
            print("┗" + "━"*78 + "┛\n")
                
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

