from flask import Flask, render_template, flash, request, session, redirect, url_for
from wtforms import Form, StringField, TextAreaField, validators, SubmitField
import requests
import json
import logging
import os

backend_addr ="http://127.0.0.1:80/"

app = Flask(__name__)
app.secret_key = 'i love white chocolate'

logging.basicConfig(level=logging.DEBUG)

@app.route("/", methods=['GET', 'POST'])
def home():
    return redirect(url_for('verify'))

@app.route("/results", methods=['GET'])
def results():
    try:
        # Make a GET request to the backend to fetch results
        resp = requests.get(f"{backend_addr}results")
        
        # Check if the request was successful (status code 200)
        resp.raise_for_status()

        # Load the response data into the result list
        result = json.loads(resp.text)

        # Sort the results by voteCount (in descending order)
        result.sort(reverse=True, key=lambda x: x["voteCount"])

        # Render the results on the HTML page
        return render_template('results.html', result=result)

    except Exception as e:
        logging.error("Error fetching results: %s", e)
        # If an error occurs, render a confirmation page with an error message
        return render_template('confirmation.html', message="Error processing results."), 500

@app.route("/verify", methods=['GET', 'POST'])
def verify():
    try:
        resp = requests.get(f"{backend_addr}isended")
        if not json.loads(resp.text):
            if request.method == 'POST':
                aid = request.form['aid']
                bio = request.form['biometric']
                if bio == 'yes' and aid.isdigit():
                    session['verified'] = True
                    session['aid'] = int(aid)
                    return redirect(url_for('vote'))
            return render_template('verification.html')
        else:
            return render_template('confirmation.html', message="Election ended", code=400), 400
    except Exception as e:
        logging.error("Error in /verify: %s", e)
        return render_template('confirmation.html', message="Error processing"), 500

@app.route("/vote", methods=['GET', 'POST'])
def vote():
    try:
        resp = requests.get(f"{backend_addr}isended")
        if not json.loads(resp.text):
            if 'verified' in session:
                resp = requests.get(f"{backend_addr}candidates_list")
                candidates = json.loads(resp.text)
                candidates1, candidates2 = candidates[:len(candidates)//2], candidates[len(candidates)//2:]
                if request.method == 'POST':
                    aid = session.pop('aid')
                    session.pop('verified')
                    candidate = request.form['candidate']
                    cid = candidates.index(candidate) + 1
                    resp = requests.post(f"{backend_addr}/", json={"aadhaarID": aid, "candidateID": cid})
                    return render_template('confirmation.html', message=resp.text, code=resp.status_code), resp.status_code
                return render_template('vote.html', candidates1=candidates1, candidates2=candidates2)
            else:
                return redirect(url_for('verify'))
        else:
            return render_template('confirmation.html', message="Election ended", code=400), 400
    except Exception as e:
        logging.error("Error in /vote: %s", e)
        return render_template('confirmation.html', message="Error processing"), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=90, debug=True)
