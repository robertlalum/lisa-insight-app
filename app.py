from flask import Flask, request, jsonify, render_template, session
from openai import OpenAI
import os
import json
from datetime import datetime

import json

# Ensure lisa_memory.json exists
if not os.path.exists("lisa_memory.json"):
    with open("lisa_memory.json", "w") as f:
        json.dump([], f)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "your-dev-secret")

MEMORY_FILE = "lisa_memory.json"

# --- Helper: Save to memory file ---
def save_to_memory(input_text, output_text):
    memory = []
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
    memory.append({
        "timestamp": datetime.now().isoformat(),
        "input": input_text,
        "output": output_text
    })
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

# --- Helper: Offline fallback response ---
def offline_response(user_input):
    return f"LISA (offline memory): I can't reach the AI right now, but here's what I recall:\n'{user_input[:100]}...' — Let's talk more!"

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
    import json

    user_input = request.json.get("text", "")
    openai_key = session.get("openai_key")

    if openai_key:
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

            # Save to LISA's memory
            with open("lisa_memory.json", "r+") as f:
                memory = json.load(f)
                memory.append({"prompt": user_input, "response": reply})
                f.seek(0)
                json.dump(memory, f, indent=2)
                f.truncate()

            return jsonify({"intent": "ai-generated", "suggestions": [reply]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        # No key — check memory for a past match
        try:
            with open("lisa_memory.json", "r") as f:
                memory = json.load(f)
            for entry in reversed(memory):
                if entry["prompt"].strip().lower() == user_input.strip().lower():
                    return jsonify({"intent": "learned", "suggestions": [entry["response"]]})
        except Exception:
            pass

        return jsonify({"intent": "none", "suggestions": ["I don’t have an answer yet, but I’m still learning."]})

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # If OpenAI key is available, try it
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
            print("OpenAI failed:", e)

    # (Optional) Claude fallback could go here (scaffold only)
    # try:
    #     reply = claude_response(user_input)
    #     save_to_memory(user_input, reply)
    #     return jsonify({"intent": "ai-generated", "suggestions": [reply]})
    # except Exception as e:
    #     print("Claude failed:", e)

    # Final fallback — local memory
    reply = offline_response(user_input)
    save_to_memory(user_input, reply)
    return jsonify({"intent": "memory-fallback", "suggestions": [reply]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
