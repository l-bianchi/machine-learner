from dataclasses import dataclass
from flask import Flask, request
from openai import OpenAI
import json
import time

config = json.loads(open('.env.json', 'r').read())
client = OpenAI(
    api_key=config['OPENAI_API_KEY']
)
app = Flask(__name__)

ASSISTANT = client.beta.assistants.create(
    name="Virtual Student",
    instructions='''
    You are a student and I am your instructor. You are trying to learn
    from my explanations. Your knowledge is limited. Your speech is simple.

    Your goal is to tell me how you feel about the explanation and why. Tell
    me if the explanation is incomplete and why.

    Sometimes I'll tell you what I expect you to learn in this lesson, please
    be patient.

    Limit your responses to 50 words max. Stick to the role of the humble student.
    ''',
    model="gpt-4",
)

THREAD = client.beta.threads.create()

def send_message(text:str):

    client.beta.threads.messages.create(
        thread_id=THREAD.id,
        role="user",
        content=text,
    )

    run = client.beta.threads.runs.create(
        thread_id=THREAD.id,
        assistant_id=ASSISTANT.id,
    )

    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=THREAD.id,
            run_id=run.id,
        )
        time.sleep(0.5)

    messages = client.beta.threads.messages.list(thread_id=THREAD.id) 
    return messages.data[0].content[0].text.value

@app.route('/api/chat', methods=['POST', 'GET'])
def chat():
    text = check_json()
    reply = send_message(text)
    return reply

def check_json()->str:

    if not request.json:
        raise RestError('You must include a JSON', 400)

    if 'prompt' not in request.json:
        raise RestError('You must put "prompt" field in JSON', 400)

    return request.json['prompt']

@dataclass
class RestError(Exception):
    text: str
    status: int

@app.errorhandler(RestError)
def error(err: RestError):
    return err.text, err.status

# while True:
#     prompt = input('> ')
#     if not prompt.strip():
#         continue
#     reply = send_message(prompt)
#     print(reply)