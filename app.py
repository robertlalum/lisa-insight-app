from flask import Flask, request, jsonify, render_template, session
import openai
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "your-dev-secret")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/set-key', methods=["POST"])
def set_key():
    key = request.json.get("key")
    if key:
        session["openai_key"] = key
        return jsonify({"message": "API key set successfully"})
    return jsonify({"error": "No key provided"}), 400

@app.route('/analyze', methods=["POST"])
def analyze():
    user_input = request.json.get("text", "")
    openai_key = session.get("openai_key")

    if not openai_key:
        return jsonify({"error": "No OpenAI key provided"}), 401

    openai.api_key = openai_key

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a negotiation assistant."},
                {"role": "user", "content": user_input}
            ]
        )
        reply = completion.choices[0].message.content
        return jsonify({"intent": "ai-generated", "suggestions": [reply]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



