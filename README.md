[Setup]
1. Set all environment variables listed in /src/config.py 
2. Launch via /src/main.py | Dockerfile | docker-compose.yml  
3. (opt) Deploy on railway 

Environment variables: 
- DEBUG creates log file, set aiogram storage to MemoryStorage  
- ASSISTANT_NAME must be specified in the database
- FILENAME must be present in the /data. Every launch would be automatically added to 'Default' vector store 
- DATABASE_URL must use async driver

It connects OpenAI so turn VPN if needed 

Notes:
- By default redis setup by private url. Commit 'file search, redis' contains docker-compose.yml to setup redis locally

[Features]
Telegram bot which can: 
- Detect mood by picture 
- Voice messaging
- Put your life values to database while voice messaging
- Analyze files for text messages 
