<div align="center">
  <a href="https://github.com/knockstick/knos-authbot">
    <img src="https://github.com/knockstick/knos-authbot/blob/main/static/logo.png?raw=true" alt="Logo" style="width: 60%; height: 60%;">
  </a>
  
  <h2 align="center">Kno's AuthBot</h2>
  <p align="center">
    Simple Discord Bot that uses OAuth2 to verify members and pull them back to the server.
  </p>
</div>

---

<b>[🇷🇺 README на русском](https://github.com/knockstick/knos-authbot/blob/main/README-ru.md/)</b>

### 🍕 Features

- Sends logs to a Discord channel
- Unlimited member pulling
- Slash commands
- Customization options
- Download and upload user database
- Supports multiple OAuth2 scopes
- Automatically updates access tokens
- Pull by country
- **100%** without CAPTCHA!
---

### 💻 Installation

[Click here to watch video tutorial](https://youtu.be/Y66Wk7iHOQY)

- `Python 3.9+` required
1. Download the repository *(if you haven't already)*
2. Create an application at the <b>[Discord Developer Portal](https://discord.com/developers)</b> and **enable all intents**
3. Edit the [config.json](https://github.com/knockstick/knos-authbot/blob/main/config.json) file and configure the HTML page in [templates folder](https://github.com/knockstick/knos-authbot/blob/main/templates)
4. Install the requirements using `pip3 install -r requirements.txt`
5. Start the bot with `python3 bot.py`

- Done! Type `/verify-embed` in your admin guild to send your verification embed to a channel.
---

### 📸 Screenshots
<img src="https://github.com/knockstick/knos-authbot/blob/main/static/oauth2scr.webp?raw=true" style="width: 40%; height: 40%;" alt="An image showing a new verified user">
<img src="https://github.com/knockstick/knos-authbot/blob/main/static/pulling.webp?raw=true" style="width: 40%; height: 40%;" alt="An image showing /pull command">
<img src="https://github.com/knockstick/knos-authbot/blob/main/static/pull.webp?raw=true" style="width: 40%; height: 40%;" alt="An image showing /pull command results">
<img src="https://github.com/knockstick/knos-authbot/blob/main/static/ui.webp?raw=true" style="width: 40%; height: 40%;" alt="The UI of the program">

---

### ❗ Disclaimer

This github repo is for **EDUCATIONAL PURPOSES ONLY.** I am not responsible for your actions.

---

### 🌟 Having troubles?
If you have an error or a problem, feel free to [start a new issue!](https://github.com/knockstick/knos-authbot/issues/new)

**OR: join my [discord server](https://discord.gg/ph85kayeuH)**

Don't forget to leave a **star!**

---
### 📰 Changelog

```diff
v 1.2.1 ⋮ 11.05.2024
+ Minor bug fixes with the new /usercheck command
+ New scope: connections: Display your user connections (like YouTube, Steam) in the log message

v1.2 ⋮ 09.05.2024
+ New command: /usercheck to remove unauthorized users and refresh access tokens
+ You can now pull by country
+ IP, access token and country are now stored in data.json
! Thanks to my Discord server members for this great ideas

v1.1 ⋮ 02.05.2024
+ Added `amount` argument to /pull command
+ You can now specify multiple guilds and verify roles in config.json
+ Better /pull stats
+ Now showing state and server name in the log
+ Login URL in /verify-embed now has a state
- Removed `log_on_end` argument from /pull command

v1.0 ⋮ 21.04.2024
! Initial release
```

---

<p align="center">
  <img src="https://img.shields.io/github/stars/knockstick/knos-authbot.svg?style=for-the-badge&labelColor=black&color=f429ff&logo=IOTA"/>
  <img src="https://img.shields.io/github/languages/top/knockstick/knos-authbot.svg?style=for-the-badge&labelColor=black&color=f429ff&logo=python"/>
</p>

---
