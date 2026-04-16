---
task: multilingual
language: mixed
---
<<

# Multilingual Template

Hello, ${name}! 👋
Bonjour, ${name}! 🇫🇷
こんにちは, ${name}! 🇯🇵
你好, ${name}! 🇨🇳
Привет, ${name}! 🇷🇺

# Emoji Support
>>
if happy:
    <<😊 You seem happy!>>
else:
    <<😐 Hope you're doing well!>>

