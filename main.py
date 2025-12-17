from yaml_reader import read_yaml_to_dict
import json
from prompt import get_prompt_conversation_llm, get_prompt_sidecar_director
from llm import talk_to_gemini, talk_to_gemini_structured

# get the API key from the .env file
import os
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

config_dict = read_yaml_to_dict('chatbot_config.yaml')


# intial prompt for the conversation LLM
to_extract = config_dict['blocks'][0]['fields']
next_extraction_block = config_dict['blocks'][1]['fields']
conversation = ""

initial_sidecar_prompt = get_prompt_sidecar_director(conversation, to_extract, next_extraction_block)
print("=== INITIAL SIDECAR PROMPT ===")
#print(initial_sidecar_prompt)

response = talk_to_gemini_structured(initial_sidecar_prompt, api_key=GEMINI_API_KEY)
#print("=== INITIAL SIDECAR RESPONSE ===")
#print(json.dumps(response.model_dump(), indent=4))

# now we need to create he conversation prompt
persona = "You are are a friendly and engaging chatbot. Keep sentences very short and concise."
conversation_prompt = get_prompt_conversation_llm(persona, conversation, response.stage_direction)
#print("=== CONVERSATION PROMPT ===")
#print(conversation_prompt)

# now we need to send the conversation prompt to the LLM
conversation_response = talk_to_gemini(conversation_prompt, api_key=GEMINI_API_KEY)
#print("=== CONVERSATION RESPONSE ===")


conversation += "You: " + conversation_response + "\n"
i=0
while True:
    print("Bot: " + conversation_response)
    user_input = input("You: ")
    conversation += "User: " + user_input + "\n"
    
    
    if i%3==0 and i!=0:
        print("=== UPDATING SIDECAR PROMPT ===")
        initial_sidecar_prompt = get_prompt_sidecar_director(conversation, to_extract, next_extraction_block)
        response = talk_to_gemini_structured(initial_sidecar_prompt, api_key=GEMINI_API_KEY)
        print("=== SIDECAR RESPONSE ===")
        print(json.dumps(response.model_dump(), indent=4))
        conversation_prompt = get_prompt_conversation_llm(persona, conversation, response.stage_direction)
    else:
        conversation_prompt = get_prompt_conversation_llm(persona, conversation, response.stage_direction)
    
    conversation_response = talk_to_gemini(conversation_prompt, api_key=GEMINI_API_KEY)
    conversation += "You: " + conversation_response + "\n"
    i+=1
