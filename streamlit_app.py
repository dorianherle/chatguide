import streamlit as st
from chat_service import ChatService
import json
from datetime import datetime


def start_chat():
    st.session_state.chat_service = ChatService()
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
    
    # Compile chat data - only prompts and replies
    chat_data = {
        "export_timestamp": datetime.now().isoformat(),
        "prompt_log": st.session_state.get("prompt_log", [])
    }
    
    # Convert to JSON string
    json_data = json.dumps(chat_data, indent=2, ensure_ascii=False)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chatguide_export_{timestamp}.json"
    
    return json_data.encode('utf-8'), filename

    

def main():
    # Password protection
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Access Required")
        st.markdown("Please enter the passcode to access the ChatGuide Demo")
        
        passcode = st.text_input("Passcode:", type="password")
        if st.button("Submit"):
            if passcode == "112233":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid passcode")
        return
    
    st.title("🤖 ChatGuide Demo")
    st.markdown("Test the conversational AI with structured task flow")
    
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
            
            # Print state to console only
            debug_info = st.session_state.chat_service.get_debug_info()
            print("[STATE]", json.dumps(debug_info, indent=2, default=str))
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Sorry, I encountered an error. Please try again."
            })

if __name__ == "__main__":
    main()
