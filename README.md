# Discord Voice Control

Host the dashboard on Vercel (project root `dashboard`, preset Other). Run the Python bot on an always-on computer with Python 3.11+. The bot listens to Discord and stores one rule per server in SQLite.

## Start the bot
1. In the Discord Developer Portal, create an application, generate a bot token and install it in the server with the bot and applications.commands scopes. Grant View Channels and Move Members in the voice channels you use.
2. Download and extract the repository. Windows users can run Start-Windows.bat and paste the token at the hidden prompt. On Linux or macOS create a virtual environment, install requirements.txt with pip, then run python bot.py. Unattended hosts can supply DISCORD_TOKEN through their environment.
3. For a custom dashboard domain set DASHBOARD_URL to its HTTPS origin before starting the bot. Use a persistent writable folder for rules.sqlite3. Existing single-target rules from the prior version are supported if the database stays beside bot.py.
4. As a Discord administrator, run /dashboard. Open the private link, paste the joining member ID, then paste up to 75 target IDs separated by whitespace or commas. Click Save rule and wait for confirmation. Reopen /dashboard to make another change. To copy an ID, enable Discord Developer Mode and choose Copy User ID on a member.
5. When the joining member enters or switches into a voice channel, the bot disconnects the listed members present there. Other channels are unaffected. Disable the rule in the dashboard or use /voice_off. The original /voice_rule command still supports a single target and an optional trigger.

Each private link authorizes one edit and expires after about 14 minutes. Keep it private. The website uses the temporary Discord interaction to pass the settings to the running bot. The bot token stays on its host. Restarting the bot ends pending editor sessions. If the connection drops before confirmation, reopen the dashboard and check the saved rule.
