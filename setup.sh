#!/bin/bash

echo ""
echo "================================"
echo "  Finmo Setup"
echo "================================"
echo ""

echo "[*] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[*] Installing dependencies..."
pip install -r requirements.txt --quiet

mkdir -p data
cp config/config.yaml.template config/config.yaml

echo ""
echo "[*] Enter your alert credentials."
echo "    Press Enter to skip any field."
echo ""

read -p "Telegram bot token: " tg_token
read -p "Telegram chat ID: " tg_chat_id
read -p "Gmail address (sender): " email_user
read -p "Gmail app password: " email_pass
read -p "Send alerts to (email): " email_to

if [ -n "$tg_token" ]; then
    sed -i "s/bot_token: \"\"/bot_token: \"$tg_token\"/" config/config.yaml
    sed -i "s/enabled: false/enabled: true/" config/config.yaml
fi
if [ -n "$tg_chat_id" ]; then
    sed -i "s/chat_id: \"\"/chat_id: \"$tg_chat_id\"/" config/config.yaml
fi
if [ -n "$email_user" ]; then
    sed -i "s/sender: \"\"/sender: \"$email_user\"/" config/config.yaml
fi
if [ -n "$email_pass" ]; then
    sed -i "s/password: \"\"/password: \"$email_pass\"/" config/config.yaml
fi
if [ -n "$email_to" ]; then
    sed -i "s/receiver: \"\"/receiver: \"$email_to\"/" config/config.yaml
fi
if [ -n "$email_user" ] && [ -n "$email_pass" ] && [ -n "$email_to" ]; then
    # enable email section (second occurrence of enabled: false)
    sed -i '0,/enabled: false/{//!b};s/enabled: false/enabled: true/' config/config.yaml
fi

echo ""
echo "[+] Setup done!"
echo ""
echo "Next steps:"
echo "  1. Edit config/config.yaml to add paths you want to monitor"
echo "  2. source venv/bin/activate"
echo "  3. python finmo.py baseline"
echo "  4. python finmo.py monitor"
echo ""
