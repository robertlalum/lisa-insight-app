from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route("/")
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    user_input = data.get("text", "").lower()

    if "price" in user_input or "cost" in user_input:
        intent = "negotiation"
        suggestions = [
            "Ask for a breakdown of costs.",
            "See if there's room for flexibility."
        ]
    elif "deadline" in user_input or "end of quarter" in user_input:
        intent = "urgency or pressure tactic"
        suggestions = [
            "Ask if this urgency changes the long-term value.",
            "Say: 'I'm here for something that lasts beyond a deadline.'"
        ]
    elif "don't know" in user_input or "maybe" in user_input:
        intent = "uncertainty"
        suggestions = [
            "Ask what's holding them back.",
            "Offer a smaller next step."
        ]
    else:
        intent = "general conversation"
        suggestions = [
            "Ask a clarifying question.",
            "Summarize what you've heard so far."
        ]

    return jsonify({
        "intent": intent,
        "suggestions": suggestions
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

@app.route('/')
def home():
    return render_template('index.html')

