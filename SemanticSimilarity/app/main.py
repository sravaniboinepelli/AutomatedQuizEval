import os
import json
from flask import Flask, flash, url_for, render_template, request, redirect, session
from semantic_text_similarity.models import WebBertSimilarity
from semantic_text_similarity.models import ClinicalBertSimilarity

app = Flask(__name__)

if __name__ == '__main__':
    port = os.getenv("SemanticSimilarity_PORT", "NOPORT")
    if port == "NOPORT":
        port = 80
    app.run('0.0.0.0', debug=True, port=int(port))

@app.route('/semantic_similarity', methods=['POST'])
def test1():
    print("Running Semantic similarity module...")
    return "Running Semantic similarity module..."

@app.route('/SemanticSimilarity', methods=['POST'])
def module():
    temp = request.get_json()
    sentences = json.loads(temp)  

    # web_model = WebBertSimilarity(device='cpu', batch_size=10) #defaults to GPU prediction
    model = ClinicalBertSimilarity(device='cpu', batch_size=10) #defaults to GPU prediction
    similarity = {}
    for x in sentences:
        print(x, sentences[x])
        predictions = model.predict([(x, sentences[x])])
        print(predictions)
        if(predictions < 2):
            similarity[x]=0
        else:
            similarity[x]=1

    # print(similarity)

    result_json = json.dumps(similarity)
    return result_json

