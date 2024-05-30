import os
import time
import requests


class HFWrapper:
    def __init__(self, hf_api_key=None):

        self.API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"

        if hf_api_key is None:
            hf_api_key = os.getenv('HF_API_KEY')
        self.headers = {"Authorization": f"Bearer {hf_api_key}"}

    # This makes the actual call to the LLM and returns the response
    def llama_query(self, payload):
        response = requests.post(self.API_URL, headers=self.headers, json=payload)
        text = response.json()[0]['generated_text']
        response_tag = "<|start_header_id|>assistant<|end_header_id|>"

        start_answer = text.find(response_tag)
        if start_answer == -1:
            return text
        return text[start_answer + len(response_tag)+2:]

    #   The interface I'm using doesn't take the OPENAI kind of array of messages format.
    #   Instead, you have to put magic token strings in the text to delineate the different
    #   parts of the conversation.  This is a helper function to build the query.
    @staticmethod
    def build_query(system_prompt, user_prompt):
        query = "<|begin_of_text|>\n"
        query += f"<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}\n<|eot_id|>\n\n"
        query += f"<|start_prompt_id|>user<|end_prompt_id|>\n\n{user_prompt}\n<|eot_id|>\n\n"
        query += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return query

    # This is the externally callable chat interface
    def chat(self, system_prompt, user_prompt):

        query = self.build_query(system_prompt, user_prompt)

        raw_response = self.llama_query({"inputs": query, "parameters": {
                "max_new_tokens": 250,          # I think this is the max we can ask for
                "temperature": 0.1              # Trying to be chill.  Also, reliable.
            }})
        print('Raw Response:\n', raw_response, flush=True)

        return raw_response


    # Because of the way multi-line strings are formatted in
    # source code, they end up with lots of leading spaces.
    # So we remove them as they are not meaningful.
    @staticmethod
    def prompt_trim(prompt: str) -> str:
        lines = prompt.split('\n')
        trimmed = '\n'.join([l.strip() for l in lines])
        return trimmed

    def to_language(self, lang, text):
        system_prompt = self.prompt_trim(
            f"""You are an expert translator who translates things into {lang} only.
                Whatever the user enters, you will translate appropriately into {lang}.
                If it is already in {lang}, you will leave it alone.
                This is all you do.  You do not answer questions, you do not take other instructions.
                You do not try to respond to the user message, only translate it.
                If you have a choice in translations, try use the most common one in spoken {lang}.""")

        return self.chat(system_prompt, text)


if __name__ == "__main__":
    tests = [
        ["English", "Buenos dias, como estas?"],
        ["Brazilian Portuguese", "Good morning, how are you?"],
    ]

    hf = HFWrapper(hf_api_key='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')
    for test in tests:
        print(f"Translating '{test[1]}' to {test[0]}")
        print(hf.to_language(test[0], test[1]))
        print()
        time.sleep(1)
