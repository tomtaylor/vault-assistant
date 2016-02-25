from flask import Flask, request
import luis
import nexmo
import os
from fuzzywuzzy import process

app = Flask(__name__)

data = [
        {
            "name": "me",
            "records": {
                "passport number": "120812981",
                "passport expiry date": "1st Jan 2018",
                "pension account number": "PENS123"
            }
        },
        {
            "name": "jane",
            "records": {
                "passport number": "9999999",
                "passport expiry date": "1st Oct 2025",
                "house insurance policy": "POLICY123"
            }
        }
    ]

@app.route('/incoming')
def handle_message():
    sender = request.args.get('msisdn')
    text = request.args.get('text')
    if sender == None or text == None:
        return "Missing required parameter"

    (intent, entities) = structure_for_raw_text(text)
    response = response_for_structure(intent, entities)
    send_response(response, sender)
    return response

def structure_for_raw_text(text):
    l = luis.Luis(url=os.environ.get("LUIS_URL"))
    r = l.analyze(text)
    b = r.best_intent()
    if b.score > 0.5:
        return (b, r.entities)
    else:
        return None

def response_for_structure(intent, entities):
    if intent == None or intent.intent != "send_data":
        return "Sorry, I don't quite understand what you want me to do."

    person = select_person(entities)
    records = select_records(person["records"], entities)
    print(records)

    if len(records) == 0:
        return "Sorry, I couldn't find anything for that."

    record_strings = []
    for key, value in records.items():
        string = "{key} is {value}".format(key=key, value=value)
        record_strings.append(string)

    if person["name"] == "me":
        person_string = "your"
    else:
        person_string = person["name"] + "'s"

    return "{person} {records}".format(person=person_string, records=" and ".join(record_strings))

def send_response(response, to):
    client = nexmo.Client(
            key=os.environ.get("NEXMO_KEY"),
            secret=os.environ.get("NEXMO_SECRET"))
    client.send_message({'from': os.environ.get("NEXMO_FROM"), 'to': to, 'text': response})

def select_person(entities):
    selected_person = None
    for person in data:
        if person["name"] == "me":
            selected_person = person
            break

    person_entities = [e for e in entities if e.type == "person"]
    person_names = [p["name"] for p in data]

    for entity in person_entities:
        (key, ratio) = process.extractOne(entity.entity, person_names)
        if ratio >= 50:
            for person in data:
                if person["name"] == key:
                    selected_person = person
                    break

    return selected_person

def select_records(records, entities):
    selected_records = {}
    subject_entities = [e for e in entities if e.type == "subject"]
    record_names = records.keys()

    for entity in subject_entities:
        (key, ratio) = process.extractOne(entity.entity, record_names)
        if ratio >= 50:
            selected_records[key] = records[key]

    return selected_records

if __name__ == "__main__":
    app.run(debug=True)
