from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize clients
anthropic = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
twilio_client = Client(
    os.environ['TWILIO_ACCOUNT_SID'],
    os.environ['TWILIO_AUTH_TOKEN']
)

# Load tooth fairy personality
with open('tooth_fairy_soul.md', 'r') as f:
    TOOTH_FAIRY_SOUL = f.read()

CONVERSATION_FILE = 'conversations.json'
AVA_PHONE = os.environ['AVA_PHONE_NUMBER']
TWILIO_PHONE = os.environ['TWILIO_PHONE_NUMBER']

def load_conversations():
    """Load conversation history from file"""
    try:
        with open(CONVERSATION_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_conversation(from_number, message, is_ava=True):
    """Save a message to conversation history"""
    conversations = load_conversations()
    conversations.append({
        'timestamp': datetime.now().isoformat(),
        'from': 'Ava' if is_ava else 'Tooth Fairy',
        'message': message
    })
    
    # Keep only last 50 messages to stay within context limits
    conversations = conversations[-50:]
    
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=2)

def build_conversation_context():
    """Build conversation history for Claude"""
    conversations = load_conversations()
    
    # Format recent conversation for context
    if not conversations:
        return []
    
    # Build message history for Claude
    messages = []
    for conv in conversations[-20:]:  # Last 20 messages
        role = "user" if conv['from'] == 'Ava' else "assistant"
        messages.append({
            "role": role,
            "content": conv['message']
        })
    
    return messages

@app.route('/sms', methods=['POST'])
def sms_webhook():
    """Handle incoming SMS from Twilio"""
    
    incoming_msg = request.form['Body']
    from_number = request.form['From']
    
    # Security: Only respond to Ava's number
    if from_number != AVA_PHONE:
        print(f"Rejected message from unauthorized number: {from_number}")
        return '', 403
    
    print(f"Received from Ava: {incoming_msg}")
    
    # Save Ava's message
    save_conversation(from_number, incoming_msg, is_ava=True)
    
    # Build conversation history
    message_history = build_conversation_context()
    
    # Add current message if not already in history
    if not message_history or message_history[-1]['content'] != incoming_msg:
        message_history.append({
            "role": "user",
            "content": incoming_msg
        })
    
    # Get response from Claude
    try:
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=TOOTH_FAIRY_SOUL,
            messages=message_history
        )
        
        reply_text = response.content[0].text
        print(f"Tooth Fairy responds: {reply_text}")
        
        # Save Tooth Fairy's response
        save_conversation(from_number, reply_text, is_ava=False)
        
        # Send SMS response
        twilio_client.messages.create(
            body=reply_text,
            from_=TWILIO_PHONE,
            to=from_number
        )
        
    except Exception as e:
        print(f"Error: {e}")
        # Send a fallback message
        twilio_client.messages.create(
            body="Oops! My fairy dust got scrambled. Try texting again! ✨",
            from_=TWILIO_PHONE,
            to=from_number
        )
    
    # Return empty response to Twilio
    return '', 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'message': 'Tooth Fairy is flying! ✨'}

if __name__ == '__main__':
    # Create conversations file if it doesn't exist
    if not os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'w') as f:
            json.dump([], f)
    
    print("🧚 Tooth Fairy server starting...")
    print(f"📱 Will respond to messages from: {AVA_PHONE}")
    app.run(debug=True, port=5000)