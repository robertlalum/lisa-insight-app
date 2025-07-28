from flask import Flask, request, jsonify, render_template, session
import openai
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "your-dev-secret")  # Change this in production

MEMORY_FILE = "lisa_memory.json"

# --- Ensure lisa_memory.json exists ---
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump([], f)

# --- Save interaction to memory file ---
def save_to_memory(input_text, output_text):
    try:
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
    except Exception as e:
        print("Failed to save memory:", e)

# --- Offline response helper ---
def offline_response(user_input):
    return f"LISA (offline memory): I can’t reach the AI right now, but I remember you said:\n‘{user_input[:100]}...’ Let’s keep talking when I’m back online."

# --- Routes ---
@app.route('/')
def home():
    return render_template('index.html')  # Make sure you have a templates/index.html

@app.route('/set-key', methods=["POST"])
def set_key():
    key = request.json.get("key")
    if key:
        session["openai_key"] = key
        return jsonify({"message": "API key set successfully"})
    return jsonify({"error": "No key provided"}), 400

@app.route('/analyze', methods=["POST"])
def analyze():
    user_input = request.json.get("text", "").strip()
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    openai_key = session.get("openai_key")

    # --- If OpenAI key is available ---
    if openai_key:
        openai.api_key = openai_key
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You're a helpful negotiation assistant."},
                    {"role": "user", "content": user_input}
                ]
            )
            reply = response.choices[0].message.content.strip()
            save_to_memory(user_input, reply)
            return jsonify({"intent": "ai-generated", "suggestions": [reply]})
        except Exception as e:
            print("OpenAI API error:", e)
            # Continue to memory fallback below

    # --- If no OpenAI key or API call failed ---
    try:
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
        for entry in reversed(memory):
            if entry["input"].strip().lower() == user_input.lower():
                return jsonify({"intent": "learned", "suggestions": [entry["output"]]})
    except Exception as e:
        print("Memory fallback error:", e)

    # --- Final fallback response ---
    reply = offline_response(user_input)
    save_to_memory(user_input, reply)
    return jsonify({"intent": "memory-fallback", "suggestions": [reply]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

        
