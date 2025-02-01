import google.generativeai as genai

class Gemini:
    model = None
    def __init__(self):
        f = open(".env", "r")
        key = f.readline()
        f.close()
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
    def prompt(self, prompt):
        return (self.model.generate_content(prompt)).text()
        
