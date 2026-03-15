# alerts.py - send alerts via Telegram and Email

import requests
import smtplib
from email.mime.text import MIMEText


def send_telegram(bot_token, chat_id, message):
    """Send a message to Telegram. Returns True if it worked."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)

        if response.status_code == 200:
            return True
        else:
            print(f"    [!] Telegram error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"    [!] Telegram error: {e}")
        return False


def send_email(smtp_host, smtp_port, sender, password, receiver, subject, body):
    """Send an email using SMTP with TLS. Returns True if it worked."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"    [!] Email error: {e}")
        return False


def build_alert_message(change_type, file_path, old_hash, new_hash, hostname, timestamp):
    """Build the alert message text for both Telegram and Email."""
    lines = []
    lines.append("FINMO ALERT")
    lines.append(f"Host:    {hostname}")
    lines.append(f"Time:    {timestamp}")
    lines.append(f"Event:   {change_type}")
    lines.append(f"File:    {file_path}")

    if change_type == "MODIFIED":
        lines.append(f"Old hash: {old_hash}")
        lines.append(f"New hash: {new_hash}")
    elif change_type == "ADDED":
        lines.append(f"Hash: {new_hash}")
    elif change_type == "DELETED":
        lines.append(f"Last known hash: {old_hash}")

    return "\n".join(lines)


def build_telegram_message(change_type, file_path, old_hash, new_hash, hostname, timestamp):
    """Build a formatted Telegram message with HTML."""
    if change_type == "MODIFIED":
        emoji = "🚨"
    elif change_type == "ADDED":
        emoji = "📄"
    else:
        emoji = "🗑️"

    lines = []
    lines.append(f"{emoji} <b>Finmo Alert</b>")
    lines.append("")
    lines.append(f"<b>Host:</b> {hostname}")
    lines.append(f"<b>Time:</b> {timestamp}")
    lines.append(f"<b>Event:</b> {change_type}")
    lines.append(f"<b>File:</b> {file_path}")

    if change_type == "MODIFIED":
        lines.append(f"<b>Old hash:</b> {old_hash[:16]}...")
        lines.append(f"<b>New hash:</b> {new_hash[:16]}...")
    elif change_type == "ADDED":
        lines.append(f"<b>Hash:</b> {new_hash[:16]}...")
    elif change_type == "DELETED":
        lines.append(f"<b>Last hash:</b> {old_hash[:16]}...")

    return "\n".join(lines)


def notify(config, change_type, file_path, old_hash, new_hash, hostname, timestamp):
    """Send alerts through all enabled channels."""
    tg = config.get("telegram", {})
    em = config.get("email", {})

    # send telegram if enabled
    if tg.get("enabled") and tg.get("bot_token") and tg.get("chat_id"):
        message = build_telegram_message(change_type, file_path, old_hash, new_hash, hostname, timestamp)
        ok = send_telegram(tg["bot_token"], tg["chat_id"], message)
        if ok:
            print(f"    [+] Telegram alert sent")

    # send email if enabled
    if em.get("enabled") and em.get("sender") and em.get("password") and em.get("receiver"):
        subject = f"[Finmo] {change_type} - {file_path} on {hostname}"
        body = build_alert_message(change_type, file_path, old_hash, new_hash, hostname, timestamp)
        ok = send_email(em["smtp_host"], em["smtp_port"], em["sender"], em["password"], em["receiver"], subject, body)
        if ok:
            print(f"    [+] Email alert sent")
