from flask import Flask, request, jsonify, render_template
import openai

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    user_input = data.get("text", "").lower()
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not api_key:
        return jsonify({"error": "Missing API key"}), 401

    openai.api_key = api_key

    try:
        # Call GPT-3.5 to get real insight
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}]
        )
        ai_reply = response.choices[0].message["content"]
    except Exception as e:
        return jsonify({"error": f"OpenAI error: {str(e)}"}), 500

    return jsonify({
        "intent": "ai response",
        "suggestions": [ai_reply]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



