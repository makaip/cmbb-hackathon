import google.generativeai as genai
f = open(".env", "r")
key = f.readline()
f.close()



class Gemini:
    model = None
    def __init__(self):
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
    def prompt(self, prompt):
        self.model.generate_content(prompt)
        
