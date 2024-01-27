from dotenv import load_dotenv
import os, requests, time
load_dotenv()
from flask import Flask, render_template, redirect, request

import pandas as pd
import google.generativeai as genai

import base64 

GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-pro-vision")
text_model = genai.GenerativeModel(model_name="gemini-pro")

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/")
def get_data():
    df = pd.read_csv('data.csv')
    df.head()

    df2 = pd.read_csv('data2.csv')
    df2.head()

    plants = []

    p_list = df['name'].tolist()
    p2 = []
    response = text_model.generate_content([
    {
        "role": 'user',
        "parts": [
          { "text": f"A person is given a choice from the following plants: {', '.join(p_list)}\nThey live in {request.form['city']}. Use this to make sure there will be enough sunlight. They want their plant to be {request.form['edible']} and want to water their plant every {request.form['water']} days, want it to look {request.form['appearance']} pretty, {request.form['usefulness']} useful, {request.form['inout']} plant, and {request.form['size']} size. They have extra comments saying they want this {request.form['comments']} in the plant. Pick exactly 10 choices from the list given above that matches this criteria. Separate your values with a comma."}
        ]
      }
    ], stream=False)
    p_list = response.text.split(", ")
    a = []
    for plant in p_list:
        row = df.iloc[df.loc[df['name'] == plant].index]
        val = row['name'].values[0]
        plants.append({
            val: 0
        })
        p2.append(val)

    descriptions = text_model.generate_content([
    {
        "role": 'user',
        "parts": [
          { "text": f"Give brief 2 sentence descriptions for each of the following plants: {', '.join(p2)}\nSeparate your values with a new line. Each line should follow the format: <plantname>: <description>"}
        ]
      }
    ], stream=False).text

    d = descriptions.splitlines()
    while True: 
        try:
            d.remove("")
        except:
            break
    d = [d.split(": ")[-1] for d in d]

    plantData = {}

    j = 0
    for i in plants:
        row = df2.iloc[df2.loc[df2['name'] == list(i.keys())[0]].index]
        plantData[list(i.keys())[0]] = {
            "ppfd": row['ppfd'].values[0],
            "photoperiod": row['photoperiod'].values[0],
            "description": d[j],
        }
        j += 1
    print(plantData)

    return render_template("result.html", data=plantData, plants=plants)


@app.post("/identify")
def identify():
    image = request.files['image']  
    ext = image.filename.split(".")[-1]
    image_string = base64.b64encode(image.read())
    imageBase64 = image_string.decode('utf-8')

    response = model.generate_content([
      {
        "role": 'user',
        "parts": [
          { "inline_data": { "mime_type": 'image/jpeg', "data": imageBase64, } },
          { "text": "Identify the invasive species in the image." }
        ]
      }
    ], stream=False)

    species = response.text

    response = text_model.generate_content([
    {
        "role": 'user',
        "parts": [
          { "text": f"Give me more details about the {species} plant species such as where it orignated form, where it is planted now, etc." }
        ]
      }
    ], stream=False)

    return render_template("identify.html", species=species, data=response.text, image=imageBase64, ext=ext)

app.run(host='0.0.0.0', port=5310, debug=True)