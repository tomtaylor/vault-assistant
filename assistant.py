from flask import Flask
import luis
import nexmo
import os

app = Flask(__name__)

@app.route('/incoming')
def handle_message():
    sender = request.args.get('msisdn')
    text = request.args.get('text')
    intent = intent_for_raw_text(text)
    response = response_for_intent(intent)
    send_response(response)
    return "OK"

def intent_for_raw_text(text):
    l = luis.Luis(url=os.environ.get("LUIS_URL"))
    r = l.analyze(text)
    b = r.best_intent()
    if b.score > 0.5:
        return b
    else:
        return None

def response_for_intent(intent):
    if intent == None or intent.intent != "send_data":
        return "Sorry, I didn't understand that."

    print(intent.entities)

    return "I am still learning how to understand this."

def send_response(response, to):
    client = nexmo.Client(key=os.environ.get("NEXMO_KEY"), secret=os.environ.get("NEXMO_SECRET"))
    client.send_message({'from': 'Vault', 'to': to, 'text': response})

if __name__ == "__main__":
    app.run()
