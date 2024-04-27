import time
import gradio as gr
from openai import OpenAI
import sys
import markdown

sys.path.append("../")
from utils.gpt_tools import *
from utils.sqlite_utils import *

USER_ID = None

def change_tab(text):
    global USER_ID
    print(text)
    USER_ID = text
    print(USER_ID)
    update_user_id(USER_ID)
    add_user(USER_ID, '123')
    refresh_user_data(USER_ID)
    return gr.Tabs(selected=1)

# # # response function
# def chat(msg,persona):
#     msg= str(msg)
#     # completion = client.chat.completions.create(
#     #     model="gpt-3.5-turbo",
#     #     messages=[
#     #     {"role": "system", "content": "You are an assistant to help the user"},
#     #     {"role": "user", "content": msg}
#     #     ]
#     # )
#     # response = completion.choices[0].message.content
#     return "ok"

def user_persona():
    persona_text = load_profile(USER_ID)
    
    if persona_text is None:
        return ""
    else:
        formatted_text = ""
        headings = ["demographics", "psychology", "experience", "marketing", "history"]
        
        for heading, text in zip(headings, persona_text):
            if text is not None:
                formatted_text += f"{heading.capitalize()}:\n{text}\n\n"
        
        return formatted_text

def extract_emails():
    file_path = r"C:/VS code projects/Makeathon/makeathon/ui/similar_history.txt"
    emails = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("Email:"):
                email = line.strip().split(": ")[1]
                emails.append("C:/VS code projects/Makeathon/makeathon/images/"+email+".jpeg")
    return emails

def email_1_return():
    return extract_emails()[0]
def email_2_return():
    return extract_emails()[1]

with gr.Blocks(
    title='test',
    css=".contain { display: flex !important; flex-direction: column !important; }"
    "#component-0, #component-3, #component-10, #component-8  { height: 80% !important; }"
    "#chatbot { flex-grow: 1 !important; overflow: auto !important;}"
    "#col { height: 90vh !important; }"
) as demo:
    
    with gr.Tabs() as tabs:
        with gr.TabItem("", id=0):
            t = gr.Textbox(label="Enter Email ID:")
        
        with gr.TabItem("", id=1):
            with gr.Row():
                gr.HTML(f" ")
            
            with gr.Row(equal_height=False):
                    
                with gr.Column(scale=2, elem_id='col'):
                    _ = gr.ChatInterface(
                        chat,
                        chatbot=gr.Chatbot(
                            show_copy_button=True,
                            render=False,
                            elem_id="chatbot",
                        ),

                    )
                    
                with gr.Column(scale=1, ): 
                    mode = gr.TextArea(
                        label="Persona",
                        value=user_persona,
                        lines=20,
                        every=1,
                    )
                    with gr.Row():
                        p1 = gr.Image(value = email_1_return,every = 1)
                        p2 = gr.Image(value = email_2_return,every = 1)


    btn = gr.Button("Submit")
    btn.click(change_tab, t,tabs)
demo.launch()