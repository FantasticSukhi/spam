# spam

### Installation

<!!!!!! VPS !!!!!!!>

1. git clone https://github.com/FantasticSukhi/spam.git
2. cd spam
3. sudo nano /etc/systemd/system/spambot.service
4. [Unit]
Description=SpamBot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/spam
ExecStart=/usr/bin/python3 /root/spam/main.py
Restart=always
RestartSec=10
StandardOutput=file:/var/log/spambot.log
StandardError=file:/var/log/spambot-error.log

[Install]
WantedBy=multi-user.target

(Copy and paste this 4th step)
[Note :- Use ctrl+o -> Enter -> ctrl+o]

5. sudo systemctl daemon-reload
6. sudo systemctl enable spambot.service
7. sudo systemctl start spambot.service
8. sudo apt update
9. sudo apt install python3 python3-pip python3-venv -y
10. python3 -m venv venv
11. source venv/bin/activate
12. pip install -r requirements.txt
13. python3 bot.py
