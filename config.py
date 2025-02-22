import json

try:
    with open("config.json", "r") as file:
        config_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    raise ValueError(f"❌ ERROR: Invalid or missing `config.json`! ({e})")


BOT_TOKEN = config_data.get("BOT_TOKEN")
SUPABASE_URL = config_data.get("SUPABASE_URL")
SUPABASE_KEY = config_data.get("SUPABASE_KEY")
CHANNEL_ID = int(config_data.get("channel_id", 0))  # Convert channel ID to integer

if not BOT_TOKEN:
    raise ValueError("❌ ERROR: Missing `BOT_TOKEN` in `config.json`!")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ ERROR: Missing Supabase credentials in `config.json`!")
