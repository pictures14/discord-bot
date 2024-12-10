import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

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

# 정보 채널 설정 명령어
@bot.tree.command(name="대룰내전_채널설정", description="대룰내전 정보를 출력할 채널을 설정합니다.")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.guild.id not in channel_settings:
        channel_settings[interaction.guild.id] = {}
    channel_settings[interaction.guild.id]["info_channel"] = channel.id
    await interaction.response.send_message(f"대룰내전 정보 채널이 설정되었습니다: {channel.mention}", ephemeral=True)

# 알림 채널 설정 명령어
@bot.tree.command(name="대룰내전_알림_채널설정", description="대룰내전 알림을 보낼 채널을 설정합니다.")
async def set_alert_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.guild.id not in channel_settings:
        channel_settings[interaction.guild.id] = {}
    channel_settings[interaction.guild.id]["alert_channel"] = channel.id
    await interaction.response.send_message(f"대룰내전 알림 채널이 설정되었습니다: {channel.mention}", ephemeral=True)

# 신청 기간 설정 명령어
@bot.tree.command(name="대룰내전_신청_기간설정", description="대룰내전 신청 가능한 기간을 설정합니다.")
async def set_application_period(interaction: discord.Interaction, 
                                 시작_날짜: str, 시작_시간: str, 종료_날짜: str, 종료_시간: str):
    try:
        start = datetime.strptime(f"{시작_날짜} {시작_시간}", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{종료_날짜} {종료_시간}", "%Y-%m-%d %H:%M")
        
        if end <= start:
            await interaction.response.send_message("종료 시간이 시작 시간보다 이전일 수 없습니다.", ephemeral=True)
            return

        application_period[interaction.guild.id] = {"start": start, "end": end}
        await interaction.response.send_message(f"신청 기간이 설정되었습니다: {start} ~ {end}", ephemeral=True)

        # 알림 채널로 메시지 전송
        guild_id = interaction.guild.id
        if guild_id in channel_settings and "alert_channel" in channel_settings[guild_id]:
            alert_channel_id = channel_settings[guild_id]["alert_channel"]
            alert_channel = bot.get_channel(alert_channel_id)

            if alert_channel:
                await alert_channel.send(
                    f"📢 **대룰내전 신청 기간 알림**\n"
                    f"신청 기간은 다음과 같습니다:\n"
                    f"🗓️ 시작: `{start.strftime('%Y-%m-%d %H:%M')}`\n"
                    f"🗓️ 종료: `{end.strftime('%Y-%m-%d %H:%M')}`\n"
                    f"지금 신청하세요!"
                )

    except ValueError:
        await interaction.response.send_message("잘못된 날짜 또는 시간 형식입니다. 'YYYY-MM-DD HH:MM' 형식으로 입력해주세요.", ephemeral=True)

# 신청 취소 명령어 (유저 이름으로)
@bot.tree.command(name="대룰내전_취소", description="대룰내전 신청을 취소합니다.")
async def cancel_application(interaction: discord.Interaction, 유저이름: str):
    guild_id = interaction.guild.id

    # 신청 정보에서 유저 이름으로 해당 정보 찾기
    if guild_id not in applications:
        await interaction.response.send_message("❌ 신청 기록이 없습니다.", ephemeral=True)
        return

    user_to_remove = None
    for user_id, data in applications[guild_id].items():
        if data["서든닉"] == 유저이름:
            user_to_remove = user_id
            break

    if user_to_remove is None:
        await interaction.response.send_message(f"❌ `{유저이름}`님은 신청하지 않았습니다.", ephemeral=True)
        return

    # 신청 정보 삭제
    del applications[guild_id][user_to_remove]
    await interaction.response.send_message(f"✅ `{유저이름}`님의 신청이 성공적으로 취소되었습니다.", ephemeral=True)

# 신청 명령어
@bot.tree.command(name="대룰내전_신청", description="대룰내전 정보를 입력받아 설정된 채널에 출력합니다.")
async def register(interaction: discord.Interaction, 
                   서든닉: str, 킬뎃: str, 디코닉네임: str, 병영링크: str):
    guild_id = interaction.guild.id
    user_id = interaction.user.id

    # 신청 기간 확인
    if guild_id in application_period:
        now = datetime.now()
        period = application_period[guild_id]
        start_time = period["start"]
        end_time = period["end"]

        if now < start_time:
            await interaction.response.send_message(
                f"❌ 신청이 아직 시작되지 않았습니다.\n"
                f"📅 신청 시작: `{start_time.strftime('%Y-%m-%d %H:%M')}`", ephemeral=True)
            return

        if now > end_time:
            await interaction.response.send_message(
                f"❌ 신청 기간이 종료되었습니다.\n"
                f"📅 신청 종료: `{end_time.strftime('%Y-%m-%d %H:%M')}`", ephemeral=True)
            return
    else:
        await interaction.response.send_message(
            "❌ 신청 기간이 설정되지 않았습니다. 관리자가 기간을 설정해야 합니다.", ephemeral=True)
        return

    # 채널 설정 여부 확인
    if guild_id not in channel_settings or "info_channel" not in channel_settings[guild_id]:
        await interaction.response.send_message("먼저 /대룰내전_채널설정 명령어로 채널을 설정해주세요.", ephemeral=True)
        return

    # 이미 신청한 유저가 있는지 확인
    if guild_id in applications and user_id in applications[guild_id]:
        await interaction.response.send_message("❌ 이미 신청한 유저는 다시 신청할 수 없습니다.", ephemeral=True)
        return

    # 설정된 정보 채널 가져오기
    channel_id = channel_settings[guild_id]["info_channel"]
    channel = bot.get_channel(channel_id)

    if not channel:
        await interaction.response.send_message("설정된 채널을 찾을 수 없습니다. 다시 설정해주세요.", ephemeral=True)
        return

    # 최대 인원 수 설정 (서버마다 다르게 설정)
    if guild_id in max_applications and len(applications[guild_id]) >= max_applications[guild_id]:
        await interaction.response.send_message("❌ 최대 신청 인원 수에 도달했습니다. 더 이상 신청할 수 없습니다.", ephemeral=True)
        return

    # 신청 데이터 저장
    if guild_id not in applications:
        applications[guild_id] = {}
    applications[guild_id][user_id] = {
        "서든닉": 서든닉,
        "킬뎃": 킬뎃,
        "디코닉네임": 디코닉네임,
        "병영링크": 병영링크
    }

    # 메시지 전송
    embed = discord.Embed(title="대룰내전 신청 정보", color=discord.Color.blue())
    embed.add_field(name="서든닉", value=서든닉, inline=False)
    embed.add_field(name="킬뎃", value=킬뎃, inline=False)
    embed.add_field(name="디코닉네임", value=디코닉네임, inline=False)
    embed.add_field(name="병영링크", value=병영링크, inline=False)
    embed.set_footer(text=f"신청자: {interaction.user.name}")

    await channel.send(embed=embed)
    await interaction.response.send_message("✅ 신청이 완료되었습니다.", ephemeral=True)

# 신청한 유저 목록 출력 명령어
@bot.tree.command(name="대룰내전_유저_목록", description="신청한 모든 사람들의 대룰내전 신청 정보를 출력합니다.")
async def show_application_list(interaction: discord.Interaction):
    guild_id = interaction.guild.id

    # 신청 정보가 없으면 메시지 전송
    if guild_id not in applications or not applications[guild_id]:
        await interaction.response.send_message("현재 신청한 사람이 없습니다.", ephemeral=True)
        return

    # 신청된 유저들의 정보 출력
    embed = discord.Embed(title="대룰내전 신청자 목록", color=discord.Color.green())
    for user_id, data in applications[guild_id].items():
        embed.add_field(name=f"신청자 {user_id}", value=f"서든닉: {data['서든닉']}\n킬뎃: {data['킬뎃']}\n디코닉네임: {data['디코닉네임']}\n병영링크: {data['병영링크']}", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# 봇 실행
bot.run("YOUR_BOT_TOKEN")
