from google import genai

class Gemini:
    client = None
    structured_output = {}
    initial_prompt = ""
    def __init__(self):
        f = open(".env", "r")
        key = f.readline()
        f.close()
        self.client = genai.Client(api_key=key)


    def prompt(self, data):
        response = self.client.models.generate_content(contents=f"{self.initial_prompt}\n{data}",
                                                       config={'response_mime_type': 'application/json',
                                                       'response_schema': self.structured_output},
                                                       model="gemini-2.0-flash-exp")
        return response.text
    # sets the default output structure
    def set_output(self, structure: type):
        self.structured_output = structure
    def set_initial_prompt(self,prompt: str):
        self.initial_prompt = prompt
