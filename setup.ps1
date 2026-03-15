Write-Host ""
Write-Host "================================"
Write-Host "  Finmo Setup"
Write-Host "================================"
Write-Host ""

Write-Host "[*] Creating virtual environment..."
python -m venv venv
.\venv\Scripts\Activate.ps1

Write-Host "[*] Installing dependencies..."
pip install -r requirements.txt --quiet

New-Item -ItemType Directory -Force -Path data | Out-Null
Copy-Item config\config.yaml.template config\config.yaml

Write-Host ""
Write-Host "[*] Enter your alert credentials."
Write-Host "    Press Enter to skip any field."
Write-Host ""

$tg_token   = Read-Host "Telegram bot token"
$tg_chat_id = Read-Host "Telegram chat ID"
$email_user = Read-Host "Gmail address (sender)"
$email_pass = Read-Host "Gmail app password"
$email_to   = Read-Host "Send alerts to (email)"

$config = Get-Content config\config.yaml
if ($tg_token)   { $config = $config -replace 'bot_token: ""', "bot_token: `"$tg_token`"" }
if ($tg_chat_id) { $config = $config -replace 'chat_id: ""', "chat_id: `"$tg_chat_id`"" }
if ($tg_token)   { $config = $config -replace 'enabled: false', 'enabled: true' -replace 'enabled: true', 'enabled: true' }
if ($email_user) { $config = $config -replace 'sender: ""', "sender: `"$email_user`"" }
if ($email_pass) { $config = $config -replace 'password: ""', "password: `"$email_pass`"" }
if ($email_to)   { $config = $config -replace 'receiver: ""', "receiver: `"$email_to`"" }
$config | Set-Content config\config.yaml

Write-Host ""
Write-Host "[+] Setup done!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit config\config.yaml to add paths to monitor"
Write-Host "  2. .\venv\Scripts\Activate.ps1"
Write-Host "  3. python finmo.py baseline"
Write-Host "  4. python finmo.py monitor"
Write-Host ""
