# Temu Bingo Telegram Bot

Bot: `@temubingo_bot`

Streamlit app: `https://temu-bingo.streamlit.app`

This Vercel webhook makes `/start` and `/play` reply with an **Open Temu Bingo** button.

## Important
Never put your Telegram bot token in GitHub.

## 1. Create a NEW GitHub repository
Recommended name: `temu-bingo-telegram-bot`

Upload the contents of this ZIP to the repository root.

```text
api/
  index.py
.gitignore
requirements.txt
vercel.json
README_START_HERE.md
```

## 2. Import the repository into Vercel
In Vercel:
1. Add New → Project
2. Import `temu-bingo-telegram-bot`
3. Keep the default framework settings
4. Add the environment variables below before deploying

## 3. Add these Vercel Environment Variables

### TELEGRAM_BOT_TOKEN
Use the token BotFather gave you for `@temubingo_bot`.
Do **not** paste it into ChatGPT or GitHub.

### TELEGRAM_WEBHOOK_SECRET
Choose a private random value using only letters, numbers, `_` or `-`.
Example format only: `TemuWebhook_7X4mQ2P9`

### SETUP_SECRET
Choose another private random value.
Example format only: `Setup_9pK4vM8x`

### APP_URL
`https://temu-bingo.streamlit.app`

Add all four to the Production environment.

## 4. Deploy
Click **Deploy**. Vercel gives you a URL similar to:

`https://temu-bingo-telegram-bot.vercel.app`

Your actual URL may differ.

## 5. Connect Telegram to the webhook — one time only
Open this in a browser:

`https://YOUR-VERCEL-DOMAIN.vercel.app/api?setup=YOUR_SETUP_SECRET`

Replace the domain and setup secret with your real values.

You should see JSON containing:

```text
"ok": true
"message": "Setup complete. Open @temubingo_bot and send /start."
```

## 6. Test
Open `https://t.me/temubingo_bot` and send:

`/start`

The bot replies with a message and a button:

`🎱 Open Temu Bingo`

The button opens `https://temu-bingo.streamlit.app`.

`/play` also works.

## 7. After setup
You can close your terminal, GitHub tab, Vercel dashboard, and laptop. The webhook runs in the cloud while the deployment remains active.

## If /start still gives no reply
Open:

`https://YOUR-VERCEL-DOMAIN.vercel.app/api`

It should show `"status": "ready"`.
Then run the setup URL again once.

## Security
The webhook verifies Telegram's `X-Telegram-Bot-Api-Secret-Token` header. The setup URL is protected by `SETUP_SECRET`.

Never share:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `SETUP_SECRET`


## Bottom-left Telegram command menu

After uploading this updated package to GitHub and Vercel redeploys it,
open your setup URL one more time:

`https://temu-bingo-telegram-bot.vercel.app/api?setup=YOUR_SETUP_SECRET`

Then Telegram's bottom-left **Menu** button will show:

- `/start` — Start Temu Bingo
- `/play` — Open the game
- `/deposit` — How to add game balance
- `/help` — Show help

`/deposit` does not collect a real-money payment. It tells the user that balance
additions are handled by the Temu Bingo admin and gives an Open Temu Bingo button.
