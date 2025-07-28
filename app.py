from flask import Flask, request, jsonify, render_template, session
from openai import OpenAI
import os
import json
from datetime import datetime

# Ensure lisa_memory.json exists
MEMORY_FILE = "lisa_memory.json"
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump([], f)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "your-dev-secret")

# Helper: Save to memory
def save_to_memory(input_text, output_text):
    try:
        with open(MEMORY_FILE, "r+") as f:
            memory = json.load(f)
            memory.append({
                "timestamp": datetime.now().isoformat(),
                "prompt": input_text,
                "response": output_text
            })
            f.seek(0)
            json.dump(memory, f, indent=2)
            f.truncate()
    except Exception as e:
        print("Error saving memory:", e)

# Fallback reply if AI is unavailable
def offline_response(user_input):
    return f"LISA (offline): I can’t reach the AI now, but here’s what I recall:\n'{user_input[:100]}…'"

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

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You're a negotiation assistant."},
                    {"role": "user", "content": user_input}
                ]
            )
            reply = response.choices[0].message.content.strip()
            save_to_memory(user_input, reply)
            return jsonify({"intent": "ai-generated", "suggestions": [reply]})
        except Exception as e:
            return jsonify({"error": f"OpenAI error: {str(e)}"}), 500

    # Try to find a learned memory fallback
    try:
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
        for entry in reversed(memory):
            if entry["prompt"].strip().lower() == user_input.strip().lower():
                return jsonify({"intent": "learned", "suggestions": [entry["response"]]})
    except Exception:
        pass

    reply = offline_response(user_input)
    save_to_memory(user_input, reply)
    return jsonify({"intent": "memory-fallback", "suggestions": [reply]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
