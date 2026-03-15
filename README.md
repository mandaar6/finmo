# Finmo — File Integrity Monitor

A simple file integrity monitoring tool that watches files and directories for unauthorized changes using SHA-256 hashing. When a change is detected it sends alerts via Telegram and/or Email.

Built with Python. Uses SQLite to store baselines and watchdog for real-time monitoring. Works on both Linux and Windows.

## What It Does

- Hashes files with SHA-256 and stores a baseline in a local SQLite database
- Monitors files in real time using watchdog (works on Linux and Windows)
- Detects file modifications, new files, and deleted files
- Sends instant alerts via Telegram and/or Gmail when changes are detected
- Keeps a record of all detected changes in the database

## Setup

### Linux / macOS

```bash
git clone https://github.com/you/finmo
cd finmo
chmod +x setup.sh
./setup.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/you/finmo
cd finmo
.\setup.ps1
```

The setup script creates a virtual environment, installs dependencies, and asks for your alert credentials.

## How to Use

Activate the virtual environment first:

```bash
# Linux/macOS
source venv/bin/activate

# Windows
.\venv\Scripts\Activate.ps1
```

Then run any of these commands:

```bash
# Create a baseline of all watched files
python finmo.py baseline

# Start real-time monitoring
python finmo.py monitor

# Compare current files against the baseline
python finmo.py diff

# Reset baseline after intentional changes (all files)
python finmo.py reset

# Reset baseline for just one file
python finmo.py reset --path /etc/nginx/nginx.conf

# Show recent detected changes
python finmo.py changes
python finmo.py changes --limit 50
```

## Configuration

Edit `config/config.yaml` to set what paths to watch and your alert credentials:

```yaml
watched_paths:
  - /etc/
  - /bin/

excluded_paths:
  - /proc/
  - "*.log"

telegram:
  enabled: true
  bot_token: "your-token"
  chat_id: "your-chat-id"

email:
  enabled: true
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  sender: "you@gmail.com"
  password: "your-app-password"
  receiver: "alerts@example.com"
```

## Setting Up Telegram Alerts

1. Open Telegram, search for **@BotFather**
2. Send `/newbot` and follow the prompts to create a bot
3. Copy the bot token you receive
4. Send any message to your new bot
5. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` in your browser
6. Find `"chat":{"id": 123456}` — that number is your chat ID
7. Put both in `config/config.yaml`

## Setting Up Email Alerts

1. Enable 2-Step Verification on your Google account
2. Go to myaccount.google.com → Security → App Passwords
3. Create a new app password for "Finmo"
4. Use that 16-character password in `config/config.yaml` (not your real password)

## Project Structure

```
finmo/
├── finmo.py             # main entry point
├── config_loader.py     # loads config.yaml
├── database.py          # SQLite operations
├── hasher.py            # SHA-256 hashing + file info
├── baseline.py          # create, reset, diff baselines
├── monitor.py           # real-time watchdog monitoring
├── alerts.py            # telegram + email alerts
├── config/
│   └── config.yaml.template
├── data/                # SQLite database (auto-created)
├── setup.sh             # Linux/macOS setup
├── setup.ps1            # Windows setup
├── requirements.txt
├── README.md
├── DISCLAIMER.md
└── .gitignore
```

## After a Restart

Your baseline and change history are saved in the SQLite database. Just activate the venv and run `python finmo.py monitor` again.

## Disclaimer

See [DISCLAIMER.md](DISCLAIMER.md). Only use on systems you own or have permission to monitor.
