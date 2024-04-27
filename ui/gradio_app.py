import time
import gradio as gr
from openai import OpenAI
import sys

sys.path.append("../")
from utils.gpt_tools import chat
client = OpenAI(api_key="")

# # response function
# def chat(msg,persona):
#     msg= str(msg)
#     completion = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#         {"role": "system", "content": "You are an assistant to help the user"},
#         {"role": "user", "content": msg}
#         ]
#     )
#     response = completion.choices[0].message.content
#     return response

with gr.Blocks(
    title='test',
    css=".contain { display: flex !important; flex-direction: column !important; }"
    "#component-0, #component-3, #component-10, #component-8  { height: 80% !important; }"
    "#chatbot { flex-grow: 1 !important; overflow: auto !important;}"
    "#col { height: 90vh !important; }"
) as demo:
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
            mode = gr.Textbox(
                label="Persona",
                value="Query Docs for Python",
            )
            with gr.Row():
                p1 = gr.Button("p1", scale = 0)
                p2 = gr.Button("p2", scale = 0)


demo.launch()