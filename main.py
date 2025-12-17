from pydantic.v1.utils import to_camel
from yaml_reader import read_yaml_to_dict
import json
from prompt import get_prompt_conversation_llm, get_prompt_sidecar_director
from llm import talk_to_gemini, talk_to_gemini_structured
import os
from dotenv import load_dotenv
from schema import ConversationResponse

class Chatbot:
    def __init__(self, config_path='chatbot_config.yaml', persona="You are a friendly and engaging chatbot. Keep sentences very short and concise. Use emojis.", debug=False):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.config = read_yaml_to_dict(config_path)
        self.persona = persona
        self.conversation = ""
        self.questions = self.config['questions']
        self.number_of_questions = 3
        self.question_index = 0

        self.sidecar_response = None
        self.debug = debug
        self.extracted_state = {}
        self.to_extract = []
        self.log_cleared = False

   

    def log(self, message):
        if self.debug:
            try:
                mode = "w" if not self.log_cleared else "a"
                with open("chatbot_log.txt", mode, encoding="utf-8") as f:
                    f.write(message + "\n")
                self.log_cleared = True
            except Exception as e:
                print(f"Logging error: {e}")

    def start(self):
        # Get first 3 questions, filtering out already extracted ones
        self.to_extract = self._get_next_questions_batch()

        # Initial setup - run sidecar to get mandate
        initial_sidecar_prompt = get_prompt_sidecar_director(self.conversation, self.extracted_state, self.to_extract)
        self.log("=== INITIAL SIDECAR PROMPT ===")
        self.log(initial_sidecar_prompt)

        self.sidecar_response = talk_to_gemini_structured(initial_sidecar_prompt, api_key=self.api_key)
        self.log("=== INITIAL SIDECAR RESPONSE ===")
        self.log(json.dumps(self.sidecar_response.model_dump(), indent=2))

        self.extracted_state.update(self.sidecar_response.extracted)

        conversation_prompt = get_prompt_conversation_llm(self.persona, self.conversation, self.sidecar_response.missing)
        self.log("=== INITIAL CONVERSATION PROMPT ===")
        self.log(conversation_prompt)

        conversation_response = talk_to_gemini_structured(conversation_prompt, api_key=self.api_key, response_schema=ConversationResponse)
        self.log("=== INITIAL CONVERSATION RESPONSE ===")
        self.log(json.dumps(conversation_response.model_dump(), indent=2))

        self.conversation += "You: " + conversation_response.response + "\n"
        return conversation_response.response

    def chat(self, user_input):
        self.conversation += "User: " + user_input + "\n"

        conversation_prompt = get_prompt_conversation_llm(self.persona, self.conversation, self.sidecar_response.missing)
        self.log("=== CONVERSATION PROMPT ===")
        self.log(conversation_prompt)

        conversation_response = talk_to_gemini_structured(conversation_prompt, api_key=self.api_key, response_schema=ConversationResponse)
        self.log("=== CONVERSATION RESPONSE ===")
        self.log(json.dumps(conversation_response.model_dump(), indent=2))

        # Update sidecar if conversation LLM indicates we got all information
        if conversation_response.got_all_information:
            self.log("=== UPDATING SIDECAR (got all information) ===")

            # Update to_extract with next batch (all questions up to new limit, minus extracted)
            self.to_extract = self._get_next_questions_batch()

            sidecar_prompt = get_prompt_sidecar_director(self.conversation, self.extracted_state, self.to_extract)
            self.log(sidecar_prompt)

            self.sidecar_response = talk_to_gemini_structured(sidecar_prompt, api_key=self.api_key)
            self.log("=== SIDECAR RESPONSE ===")
            self.log(json.dumps(self.sidecar_response.model_dump(), indent=2))

            self.extracted_state.update(self.sidecar_response.extracted)

            print("=== SIDECAR RESPONSE ===")
            print(json.dumps(self.sidecar_response.model_dump(), indent=4))

            # update conversation response
            conversation_prompt = get_prompt_conversation_llm(self.persona, self.conversation, self.sidecar_response.missing)
            self.log("=== UPDATED CONVERSATION PROMPT ===")
            self.log(conversation_prompt)

            conversation_response = talk_to_gemini_structured(conversation_prompt, api_key=self.api_key, response_schema=ConversationResponse)
            self.log("=== UPDATED CONVERSATION RESPONSE ===")
            self.log(json.dumps(conversation_response.model_dump(), indent=2))

        self.conversation += "You: " + conversation_response.response + "\n"


        return conversation_response.response

    def _get_next_questions_batch(self):
        """Get all questions up to current batch, excluding those already extracted."""
        # Get all questions from start up to current batch end
        next_batch = self.questions[0:self.question_index + self.number_of_questions]
        self.question_index += self.number_of_questions

        # Filter out questions that are already extracted
        # q is a dict like {"name": "The name"}, check if its key is not in extracted_state
        filtered_batch = [q for q in next_batch if list(q.keys())[0] not in self.extracted_state]

        return filtered_batch

# Usage example
if __name__ == "__main__":
    # Clear log file at start
    with open("chatbot_log.txt", "w", encoding="utf-8") as f:
        f.write("")

    bot = Chatbot(debug=True)
    response = bot.start()

    while True:
        try:
            print("Bot: " + response)
        except UnicodeEncodeError:
            print("Bot: " + response.encode('ascii', 'ignore').decode('ascii'))
        try:
            user_input = input("You: ")
        except KeyboardInterrupt:
            break
        response = bot.chat(user_input)
