import time
import random
import google.generativeai as genai
import PIL.Image

class Agent:
    def __init__(self, model_name: str, name: str, temperature: float, sleep_time: float=1) -> None:
        self.model_name = model_name
        self.name = name
        self.temperature = temperature
        self.memory_lst = ""
        self.sleep_time = sleep_time


    def query(self, prompt: str, api_key: str, image_file: str) -> str:
        time.sleep(1)

        genai.configure(api_key=api_key, transport='rest')  # add your api_key
        model = genai.GenerativeModel(model_name="gemini-pro-vision")
        img = PIL.Image.open(image_file)
        ff = False
        step = 0
        while ff == False or step < 5:
            try:
                response = model.generate_content([prompt, img])
                response.resolve()
                ff = True
                break
            except:
                time.sleep(1)
                step += 1
        if ff == True:
            try:
                return response.text
            except:
                return "error"
        else:
            return "error"

    def set_meta_prompt(self, meta_prompt: str):
        self.memory_lst = self.memory_lst + '\n' + meta_prompt

    def add_event(self, event: str):
        self.memory_lst = self.memory_lst + '\n' + event

    def add_memory(self, memory: str):
        self.memory_lst = self.memory_lst + '\n' + memory
        print(f"----- {self.name} -----\n{memory}\n")

    def ask(self, image_file: str):
        return self.query(self.memory_lst, api_key=self.google_api_key, image_file = image_file) # query

