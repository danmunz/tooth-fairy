# 🧚 Tooth Fairy SMS Bot

An AI-powered SMS bot that lets children text with the Tooth Fairy! Built with Claude (Anthropic), DALL-E (OpenAI), and Twilio.

## ✨ Features

- **AI-Powered Responses**: Uses Claude to generate warm, magical responses in the Tooth Fairy's voice
- **Image Generation**: Can send AI-generated "selfies" and pictures using DALL-E
- **Multi-User Support**: Multiple family members can text (child + parents)
- **Conversation Memory**: Remembers past conversations for context
- **Daily Image Limits**: Prevents excessive API costs with configurable limits
- **Admin Commands**: Parents can check stats and history
- **Customizable Personality**: Define the Tooth Fairy's character via a markdown file

## 🎯 Use Case

Create magical childhood memories by letting your child text directly with the Tooth Fairy. Parents can also participate behind the scenes to provide context or monitor conversations.

## 💰 Cost Estimate

- **Twilio Phone Number**: ~$1/month
- **SMS Messages**: $0.0075 per message (both ways)
- **Claude API**: ~$0.003 per response
- **DALL-E 3 Images**: $0.04 per image (standard quality)

**Total**: ~$2-5/month for typical usage

## 🛠 Tech Stack

- **Backend**: Python + Flask
- **AI**: Anthropic Claude Sonnet 4
- **Images**: OpenAI DALL-E 3
- **SMS**: Twilio
- **Hosting**: Render (or any Python hosting service)

## 📋 Prerequisites

- Python 3.11+
- Twilio account (free trial available)
- Anthropic API key
- OpenAI API key

## 🚀 Setup

### 1. Clone and Install Dependencies

```bash
git clone <your-repo>
cd tooth-fairy
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Twilio

1. Sign up at [twilio.com](https://www.twilio.com/try-twilio)
2. Buy a toll-free phone number (~$1/month)
3. Complete toll-free verification (describe it as a personal family project)
4. Save your Account SID, Auth Token, and phone number

### 3. Get API Keys

- **Anthropic**: Get your API key from [console.anthropic.com](https://console.anthropic.com/)
- **OpenAI**: Get your API key from [platform.openai.com](https://platform.openai.com/api-keys)

### 4. Configure Environment Variables

Create a `.env` file:

```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+18001234567

# Allowed phone numbers (include country code)
CHILD_PHONE_NUMBER=+17031234567
PARENT1_PHONE_NUMBER=+17031234568
PARENT2_PHONE_NUMBER=+17031234569

# Settings
DAILY_IMAGE_LIMIT=5
```

**Important**: Phone numbers must include country code (e.g., `+1` for US) with no spaces or dashes.

### 5. Customize the Personality

Edit `tooth_fairy_soul.md` to customize:
- Name and pronouns
- Personality traits
- Appearance
- Texting style
- Topics of interest
- Information about your child

### 6. Test Locally

```bash
# Terminal 1: Start the server
python app.py

# Terminal 2: Expose with ngrok
ngrok http 5000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

### 7. Configure Twilio Webhook

1. Go to Twilio Console → Phone Numbers → Your Number
2. Under "Messaging Configuration"
3. Set "A MESSAGE COMES IN" webhook to: `https://abc123.ngrok.io/sms`
4. Save

### 8. Test It!

Text your Twilio number from an allowed phone and get a magical response! ✨

## 🌐 Deploy to Production

### Using Render (Recommended)

1. Push your code to GitHub
2. Sign up at [render.com](https://render.com)
3. Create a new Web Service
4. Connect your repository
5. Add all environment variables from `.env`
6. Deploy!
7. Update Twilio webhook to your Render URL: `https://your-app.onrender.com/sms`

### Other Options

- AWS Lambda + API Gateway
- Railway
- Fly.io
- Heroku
- Any Python WSGI hosting

## 📱 Usage

### For Children

Just text the Tooth Fairy number! The bot will:
- Respond in character
- Remember past conversations
- Send pictures when appropriate
- Celebrate tooth milestones

### For Parents

**Normal texting**: Just text like the child would. The Tooth Fairy will acknowledge parent messages subtly.

**Admin Commands** (start message with `!`):
- `!stats` - View conversation statistics
- `!history` - See recent messages  
- `!help` - List available commands

Example:
```
Parent: !stats

Tooth Fairy: 📊 Tooth Fairy Stats:
Total messages: 47
Images today: 3/5
Last message: 2026-01-31T14:23:10
Allowed users: child, parent1, parent2
```

## 🎨 Customization

### Adjust Image Limit

Change `DAILY_IMAGE_LIMIT` in `.env` or modify the constant in `app.py`:

```python
DAILY_IMAGE_LIMIT = 5  # Change this number
```

### Modify Personality

Edit `tooth_fairy_soul.md` to change:
- Character traits
- Speaking style
- Knowledge about your child
- Boundaries and guidelines

### Change Image Style

Modify the `create_image_prompt()` function in `app.py` to adjust DALL-E prompts.

### Add More Users

Add phone numbers to `.env`:

```env
GRANDPARENT_PHONE_NUMBER=+15551234567
```

Then update `ALLOWED_NUMBERS` in `app.py`:

```python
ALLOWED_NUMBERS = {
    'child': os.environ.get('CHILD_PHONE_NUMBER', ''),
    'parent1': os.environ.get('PARENT1_PHONE_NUMBER', ''),
    'parent2': os.environ.get('PARENT2_PHONE_NUMBER', ''),
    'grandparent': os.environ.get('GRANDPARENT_PHONE_NUMBER', ''),
}
```

## 🔒 Security

- Only phone numbers in `.env` can interact with the bot
- All API keys are stored securely in environment variables
- Conversation history is stored locally in `conversations.json`
- `.gitignore` prevents committing sensitive data

## 📊 Monitoring

### Health Check Endpoint

```bash
curl https://your-app.onrender.com/health
```

Returns:
```json
{
  "status": "ok",
  "message": "Tooth Fairy is flying! ✨",
  "images_today": 2,
  "daily_limit": 5,
  "allowed_users": ["child", "parent1", "parent2"]
}
```

### Logs

- **Local**: Check terminal output
- **Render**: View logs in Render dashboard
- **Twilio**: Check message logs in Twilio console

## 🐛 Troubleshooting

**"Authentication failed" with ngrok**
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

**"Toll-free verification required"**
- Fill out Twilio's verification form
- Describe as personal family project
- Wait 24-48 hours for approval

**Bot not responding**
- Check webhook URL in Twilio console
- Verify phone numbers in `.env` match format: `+1XXXXXXXXXX`
- Check logs for errors

**Images not generating**
- Verify OpenAI API key is valid
- Check you haven't hit daily image limit
- Ensure you have OpenAI credits

## 🔄 Conversation History

Conversations are stored in `conversations.json` with this format:

```json
{
  "timestamp": "2026-01-31T14:30:00",
  "from": "Child",
  "phone": "+17031234567",
  "message": "I lost a tooth!",
  "image_url": null
}
```

To reset conversations, delete or clear this file.

## 🎁 Enhancement Ideas

- **Scheduled messages**: Tooth Fairy texts first sometimes
- **Voice calls**: Use Twilio Voice API
- **Tooth tracking**: Database of which teeth have been lost
- **Special events**: Automatic messages on birthdays
- **Parent dashboard**: Web interface to view conversations
- **Multiple tooth fairies**: Different personalities for siblings

## 📝 License

This is a personal project. Feel free to adapt for your own family!

## 🙏 Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/)
- [OpenAI DALL-E](https://openai.com/dall-e-3)
- [Twilio](https://www.twilio.com/)
- Flask, Python, and lots of fairy dust ✨

---

**Note**: This project creates magical experiences for children. Use responsibly and always prioritize their well-being and privacy.
