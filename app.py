from flask import Flask, request
from twilio.rest import Client
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize clients
anthropic = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
twilio_client = Client(
    os.environ['TWILIO_ACCOUNT_SID'],
    os.environ['TWILIO_AUTH_TOKEN']
)

# Load tooth fairy personality
with open('tooth_fairy_soul.md', 'r') as f:
    TOOTH_FAIRY_SOUL = f.read()

CONVERSATION_FILE = 'conversations.json'
TWILIO_PHONE = os.environ['TWILIO_PHONE_NUMBER']
DAILY_IMAGE_LIMIT = int(os.environ.get('DAILY_IMAGE_LIMIT', 5))

# Allowed phone numbers - load from environment
ALLOWED_NUMBERS = {
    'ava': os.environ.get('AVA_PHONE_NUMBER', ''),
    'dan': os.environ.get('DAN_PHONE_NUMBER', ''),
    'wife': os.environ.get('WIFE_PHONE_NUMBER', '')
}

# Remove any empty entries
ALLOWED_NUMBERS = {k: v for k, v in ALLOWED_NUMBERS.items() if v}

def get_sender_name(phone_number):
    """Get the name of the person texting"""
    for name, number in ALLOWED_NUMBERS.items():
        if number == phone_number:
            return name.capitalize()
    return "Unknown"

def is_parent(phone_number):
    """Check if the sender is a parent (not Ava)"""
    sender = get_sender_name(phone_number)
    return sender.lower() in ['dan', 'wife']

def load_conversations():
    """Load conversation history from file"""
    try:
        with open(CONVERSATION_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_conversation(from_number, message, is_from_user=True, image_url=None):
    """Save a message to conversation history"""
    conversations = load_conversations()
    sender_name = get_sender_name(from_number) if is_from_user else 'Tooth Fairy'
    
    conversations.append({
        'timestamp': datetime.now().isoformat(),
        'from': sender_name,
        'phone': from_number if is_from_user else TWILIO_PHONE,
        'message': message,
        'image_url': image_url
    })
    
    # Keep only last 50 messages
    conversations = conversations[-50:]
    
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=2)

def get_images_sent_today():
    """Count how many images have been sent today"""
    conversations = load_conversations()
    today = datetime.now().date()
    
    count = sum(1 for c in conversations 
                if c.get('image_url') 
                and datetime.fromisoformat(c['timestamp']).date() == today
                and c.get('from') == 'Tooth Fairy')
    
    return count

def build_conversation_context(current_sender):
    """Build conversation history for Claude"""
    conversations = load_conversations()
    
    if not conversations:
        return []
    
    messages = []
    for conv in conversations[-20:]:
        # Determine role based on who sent it
        role = "assistant" if conv['from'] == 'Tooth Fairy' else "user"
        
        # Format message with sender name if not Ava
        content = conv['message']
        if conv['from'] != 'Ava' and conv['from'] != 'Tooth Fairy':
            # Prefix parent messages
            content = f"[Message from {conv['from']}]: {content}"
        
        if conv['from'] not in ['Ava', 'Tooth Fairy']:
            # Parent messages - include in context but mark as [CONTEXT ONLY]
            content = f"[BACKGROUND INFO - Don't mention this explicitly]: {content}"

        # Note if an image was sent
        if conv.get('image_url'):
            content += " [sent image]"
        
        messages.append({
            "role": role,
            "content": content
        })
    
    return messages

def generate_tooth_fairy_image(prompt):
    """Generate an image using DALL-E"""
    try:
        print(f"Generating image with prompt: {prompt}")
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        print(f"Generated image URL: {image_url}")
        return image_url
    
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

def should_send_image(message):
    """Check if the message suggests sending an image"""
    image_triggers = [
        'selfie', 'picture', 'photo', 'show you', 'look like',
        'see me', 'what i look like', 'send you a pic', 'send a pic'
    ]
    
    message_lower = message.lower()
    return any(trigger in message_lower for trigger in image_triggers)

def create_image_prompt(tooth_fairy_message):
    """Create a DALL-E prompt based on Tooth Fairy's message"""
    message_lower = tooth_fairy_message.lower()
    
    # Base prompt for the Tooth Fairy
    base = "A whimsical, magical tooth fairy character, "
    
    # Contextual additions
    if 'flying' in message_lower or 'fly' in message_lower:
        context = "flying through a starlit night sky with magical sparkles trailing behind, "
    elif 'collecting' in message_lower or 'teeth' in message_lower:
        context = "collecting shiny teeth with a small magical bag, "
    elif 'palace' in message_lower or 'home' in message_lower:
        context = "in a beautiful crystal palace made of teeth and stars, "
    else:
        context = "with delicate wings and a warm smile, surrounded by fairy dust and sparkles, "
    
    # Style
    style = "children's book illustration style, warm and friendly, magical atmosphere, soft lighting"
    
    full_prompt = base + context + style
    
    return full_prompt

@app.route('/sms', methods=['POST'])
def sms_webhook():
    """Handle incoming SMS from Twilio"""
    
    incoming_msg = request.form['Body']
    from_number = request.form['From']
    
    # Security: Check if number is allowed
    if from_number not in ALLOWED_NUMBERS.values():
        print(f"Rejected message from unauthorized number: {from_number}")
        return '', 403
    
    sender_name = get_sender_name(from_number)
    print(f"Received from {sender_name}: {incoming_msg}")
    
    # Check for admin commands (parents only)
    if is_parent(from_number) and incoming_msg.startswith('!'):
        return handle_admin_command(incoming_msg, from_number)
    
    # Save sender's message
    save_conversation(from_number, incoming_msg, is_from_user=True)
    
    # Build conversation history
    message_history = build_conversation_context(sender_name)
    
    # Add current message if not already in history
    current_content = incoming_msg
    if sender_name != 'Ava':
        current_content = f"[Message from {sender_name}]: {incoming_msg}"
    
    if not message_history or message_history[-1]['content'] != current_content:
        message_history.append({
            "role": "user",
            "content": current_content
        })
    
    # Enhanced system prompt
    enhanced_system = TOOTH_FAIRY_SOUL + f"""

## Current Conversation Context
You are currently responding to a message from {sender_name}.
- If it's from Ava, respond as you normally would
- If it's from Dan or his wife (Ava's parents), acknowledge them subtly but stay in character
  - You might say things like "I know you're checking in on us! 😊"
  - Or "Thanks for helping me understand Ava better!"
  - Keep it magical but acknowledge the adult in the room

## Image Capabilities
You can send images! When appropriate, you can offer to send a picture or selfie.
- If Ava asks for a picture/selfie, respond warmly and say you'll send one
- You can also occasionally offer to send pictures of your adventures
- Keep it natural - not every message needs an image
- When you decide to send an image, include phrases like:
  - "Let me send you a selfie!"
  - "Here's a picture of what I'm seeing"
  - "Want to see where I am?"
"""
    
    # Get response from Claude
    try:
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=enhanced_system,
            messages=message_history
        )
        
        reply_text = response.content[0].text
        print(f"Tooth Fairy responds: {reply_text}")
        
        # Check if we should generate an image
        image_url = None
        images_today = get_images_sent_today()
        
        if should_send_image(reply_text):
            print(f"Tooth Fairy wants to send an image! (Already sent {images_today} today)")
            
            if images_today < DAILY_IMAGE_LIMIT:
                # Create prompt from context
                image_prompt = create_image_prompt(reply_text)
                image_url = generate_tooth_fairy_image(image_prompt)
            else:
                # Hit the daily limit - send battery message
                print(f"Daily image limit reached ({DAILY_IMAGE_LIMIT})")
                battery_msg = "Whoopsie Ava, my camera ran out of battery! 📸✨ I'll recharge it and send you pictures tomorrow!"
                
                # Send the battery message as a follow-up
                twilio_client.messages.create(
                    body=battery_msg,
                    from_=TWILIO_PHONE,
                    to=from_number
                )
                
                # Save the battery message to conversation history
                save_conversation(from_number, battery_msg, is_from_user=False)
        
        # Save Tooth Fairy's response
        save_conversation(from_number, reply_text, is_from_user=False, image_url=image_url)
        
        # Send text response
        twilio_client.messages.create(
            body=reply_text,
            from_=TWILIO_PHONE,
            to=from_number
        )
        
        # Send image if generated
        if image_url:
            twilio_client.messages.create(
                media_url=[image_url],
                from_=TWILIO_PHONE,
                to=from_number
            )
            print(f"Image sent! ({images_today + 1}/{DAILY_IMAGE_LIMIT} today)")
        
    except Exception as e:
        print(f"Error: {e}")
        twilio_client.messages.create(
            body="Oops! My fairy dust got scrambled. Try texting again! ✨",
            from_=TWILIO_PHONE,
            to=from_number
        )
    
    return '', 200

def handle_admin_command(command, from_number):
    """Handle special admin commands for parents"""
    cmd = command.lower().strip()
    
    if cmd == '!stats':
        # Get conversation stats
        conversations = load_conversations()
        images_today = get_images_sent_today()
        total_messages = len(conversations)
        
        stats_msg = f"""📊 Tooth Fairy Stats:
        
Total messages: {total_messages}
Images today: {images_today}/{DAILY_IMAGE_LIMIT}
Last message: {conversations[-1]['timestamp'] if conversations else 'None'}

Allowed users: {', '.join(ALLOWED_NUMBERS.keys())}"""
        
        twilio_client.messages.create(
            body=stats_msg,
            from_=TWILIO_PHONE,
            to=from_number
        )
        
    elif cmd == '!history':
        # Get recent conversation summary
        conversations = load_conversations()
        recent = conversations[-10:]
        
        history_msg = "📜 Recent Messages:\n\n"
        for conv in recent:
            history_msg += f"{conv['from']}: {conv['message'][:50]}...\n"
        
        twilio_client.messages.create(
            body=history_msg,
            from_=TWILIO_PHONE,
            to=from_number
        )
    
    elif cmd == '!help':
        help_msg = """🧚 Admin Commands:
        
!stats - View conversation statistics
!history - View recent messages
!help - This message

Just text normally to chat with the Tooth Fairy!"""
        
        twilio_client.messages.create(
            body=help_msg,
            from_=TWILIO_PHONE,
            to=from_number
        )
    
    return '', 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'ok', 
        'message': 'Tooth Fairy is flying! ✨',
        'images_today': get_images_sent_today(),
        'daily_limit': DAILY_IMAGE_LIMIT,
        'allowed_users': list(ALLOWED_NUMBERS.keys())
    }

if __name__ == '__main__':
    # Create conversations file if it doesn't exist
    if not os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'w') as f:
            json.dump([], f)
    
    print("🧚 Tooth Fairy server starting...")
    print(f"📱 Allowed users: {', '.join(ALLOWED_NUMBERS.keys())}")
    print(f"📸 Image generation enabled! (Daily limit: {DAILY_IMAGE_LIMIT})")
    app.run(debug=True, port=5000)
```

## Update Your `.env` File

Add the additional phone numbers:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+18001234567
DAILY_IMAGE_LIMIT=5

# Allowed phone numbers
AVA_PHONE_NUMBER=+17031234567
DAN_PHONE_NUMBER=+17031234568
WIFE_PHONE_NUMBER=+17031234569
```

## Key Features

### 1. **Multi-User Support**
- Anyone in `ALLOWED_NUMBERS` can text
- Each message is tagged with sender's name
- Conversation history preserves who said what

### 2. **Parent-Aware Responses**
The Tooth Fairy will subtly acknowledge when a parent texts:
```
Dan: "Ava lost her first molar today!"
Tooth Fairy: "Oh wonderful! Thanks for letting me know! I'll make sure to give that one extra attention tonight ✨"
```

### 3. **Admin Commands** (Parents Only)
Text these commands to get info:

- `!stats` - View conversation statistics
- `!history` - See recent messages
- `!help` - List available commands

Example:
```
Dan: !stats

Tooth Fairy: 📊 Tooth Fairy Stats:
Total messages: 47
Images today: 3/5
Last message: 2026-01-31T14:23:10
Allowed users: ava, dan, wife