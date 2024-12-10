import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os  # 환경 변수에서 토큰을 불러오기 위해 추가

# 봇 초기화
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='/', intents=intents)

# 저장 변수
channel_settings = {}  # {guild_id: {"info_channel": channel_id, "alert_channel": channel_id}}
application_period = {}  # {guild_id: {"start": datetime, "end": datetime}}
applications = {}  # {guild_id: {user_id: application_data}}
max_applications = {}  # {guild_id: max_application_count}

# 봇 준비
@bot.event
async def on_ready():
    print(f'봇이 로그인되었습니다: {bot.user}')
    try:
        synced = await bot.tree.sync()  # Slash 명령어 동기화
        print(f'명령어가 동기화되었습니다: {len(synced)}개')
    except Exception as e:
        print(f'명령어 동기화 실패: {e}')

# 여기에 나머지 명령어 코드 추가
# ...

# 봇 실행
bot.run(os.getenv("DISCORD_BOT_TOKEN"))  # 환경 변수에서 토큰 불러오기

