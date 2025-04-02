import google.generativeai as genai

class Gemini:
    model = None
    structured_output = ""
    initial_prompt = ""
    def __init__(self):
        f = open(".env", "r")
        key = f.readline()
        f.close()
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")


    def prompt(self, data):
        response = self.model.generate_content(f"{self.initial_prompt}\nFollow this JSON schema: {self.structured_output}\n{data}")
        return response.text
    # sets the default output structure
    def set_output(self, structure: str):
        self.structured_output = structure
    def set_initial_prompt(self,prompt: str):
        self.initial_prompt = prompt
