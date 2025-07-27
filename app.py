import os
from flask import Flask, request, jsonify, render_template
import openai

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    user_input = data.get("text", "").strip()
    api_key = data.get("api_key", "").strip()

    # Default simple keyword-based fallback logic
    def simple_response(text):
        text = text.lower()
        if "price" in text or "cost" in text:
            return {
                "intent": "negotiation",
                "suggestions": [
                    "Ask for a breakdown of costs.",
                    "See if there's room for flexibility."
                ]
            }
        elif "deadline" in text or "end of quarter" in text:
            return {
                "intent": "urgency or pressure tactic",
                "suggestions": [
                    "Ask if this urgency changes the long-term value.",
                    "Say: 'I'm here for something that lasts beyond a deadline.'"
                ]
            }
        elif "don't know" in text or "maybe" in text:
            return {
                "intent": "uncertainty",
                "suggestions": [
                    "Ask what's holding them back.",
                    "Offer a smaller next step."
                ]
            }
        else:
            return {
                "intent": "general conversation",
                "suggestions": [
                    "Ask a clarifying question.",
                    "Summarize what you've heard so far."
                ]
            }

    if api_key:
        # Use OpenAI GPT for better analysis
        openai.api_key = api_key
        try:
            prompt = f"""
            You are LISA, a helpful conversation assistant. Analyze the user's text and return the intent and suggestions.
            Text: "{user_input}"
            Respond in JSON with two fields: intent (short string) and suggestions (list of short strings).
            """

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
            )
            result_text = response.choices[0].message.content.strip()

            # Try to parse JSON from the result
            import json
            result_json = json.loads(result_text)
            return jsonify(result_json)

        except Exception as e:
            # If something goes wrong, fallback to simple
            fallback = simple_response(user_input)
            fallback["error"] = str(e)
            return jsonify(fallback)
    else:
        # No API key provided, fallback to simple logic
        return jsonify(simple_response(user_input))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)



