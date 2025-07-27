from flask import Flask, request, jsonify, render_template, session
import openai
import anthropic
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

ANTHROPIC_KEY = os.environ.get("CLAUDE_API_KEY")  # Set this in your Render or local .env

# Claude setup (optional)
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

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

    if not user_input.strip():
        return jsonify({"error": "No input provided"}), 400

    reply = "No AI model available for response."
    model_used = "none"

    try:
        # Try OpenAI first if key is present
        if openai_key:
            openai.api_key = openai_key
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You're a negotiation assistant."},
                    {"role": "user", "content": user_input}
                ]
            )
            reply = completion.choices[0].message.content
            model_used = "openai-gpt-4"

        # Try Claude if no OpenAI key but Claude key is available
        elif ANTHROPIC_KEY:
            claude_response = claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": user_input}]
            )
            reply = claude_response.content[0].text
            model_used = "claude-3-opus"

        # Record what LISA sees and learns
        record_learning(user_input, reply, model_used)

        return jsonify({"intent": "ai-generated", "suggestions": [reply]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔍 Logs everything LISA hears and sees into a .jsonl file
def record_learning(user_input, reply, model_used):
    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": user_input,
        "reply": reply,
        "model": model_used
    }
    with open("lisa_learning_log.jsonl", "a") as f:
        f.write(json.dumps(log) + "\n")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
