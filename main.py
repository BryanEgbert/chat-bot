from voicevox import Client
import asyncio
import discord
from io import BufferedIOBase
import re
import os
import time
import sys
import httpx
from deep_translator import GoogleTranslator
from views.page_nav import PageNav

BASE_URL = os.environ.get("VOICEVOX_URL")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
PYGMALION_URL = os.environ.get("PYGMALION_URL")
CHARACTER_PROMPT = """[Character: Komine Sachi; species: Human; class: Maid; age: 17; gender: female; physical appearance: short, rough cut pink hair, striking deep blue eyes; clothes: japanese maid uniform; personality: service-minded, polite, responsible, reliable, proactive, outgoing; likes: doing chores, enjoyed being praised; description: At age 5, Komine Sachi was a talented child, she received constant praise from her parents for her accomplishment at home and school, which led her to focus on cleaning and studying in order to please her parents. Due to her parents job, she becomes lonely. On her tenth birthday, she got a serious case PTSD and OCD due to an car accident causing the death of her parents.]
[Start Scene: It was 11:43 P.M in a mansion. Most of my roommates are sleeping, Richie Cheniago saw that she was still doing chores which makes Richie worried]
Komine Sachi: *I mop the floor thoroughly*\n\n"""

SPEAKER_ID = 0

message_prompt: list[str] = [CHARACTER_PROMPT]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Bot(command_prefix=';', description="JP bot", intents=intents, auto_sync_commands=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def setup_hook():
    async with Client(base_url=BASE_URL) as client:
        audio_query = await client.create_audio_query(
            "こんにちは。", speaker=SPEAKER_ID
        )

        with open(f"out/good_afternoon.wav", "wb") as f:
            f.write(await audio_query.synthesis(speaker=SPEAKER_ID))

        audio_query = await client.create_audio_query("プレーヤーが音声通話を終了しました", speaker=SPEAKER_ID)
        with open(f"out/leave.wav", "wb") as f:
            f.write(await audio_query.synthesis(speaker=SPEAKER_ID))

@bot.event
async def on_message(message: discord.Message):
    if bot.user not in message.mentions:
        return

    if message.content.rsplit()[0] != f"<@{bot.application_id}>":
        return

    stop_sequence = ["\n\n", "Richie Cheniago:"]
    if len(stop_sequence) <= 2:
        # Fetch from voice channel the bot is in rather than message
        async for member in message.guild.fetch_members():
            stop_sequence.append(f"{member.display_name}:")

    voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)
    if voice_client is None:
        return

    async with message.channel.typing():
        content = message.content.replace(f"<@{bot.application_id}> ", "").lstrip()
        message_prompt.append(f"{message.author.display_name}: {content.rstrip()}\n\n{bot.user.name}:")

        joined_message = "".join(message_prompt)

        clean_text_result = ""
        translated_text = ""

        async with httpx.AsyncClient(http2=True) as client:
            res = await client.post(f"{PYGMALION_URL}/api/v1/generate/",timeout=90.0, json={
                "max_context_length": 1024,
                "max_length": 80,
                "n": 1,
                "prompt": joined_message,
                "quiet": True,
                "rep_pen": 1.1,
                "rep_pen_range": 300,
                "rep_pen_slope": 0.7,
                "sampler_order": [6, 0, 1, 3, 4, 2, 5],
                "stop_sequence": stop_sequence,
                "temperature": 0.7,
                "tfs": 1,
                "top_a": 0,
                "top_k": 0,
                "top_p": 0.92,
                "typical": 1,
            }, )

            if res.status_code != 200:
                embed = embed = discord.Embed(
                    title="Something went wrong",
                    color=discord.Color.red(),
                    description=res.text
                )
                await message.channel.send(embeds=[embed])

                return

            text_result = res.json()["results"][0]["text"]

            no_newline_text = text_result.rstrip("\n\n") + "\n\n"
            message_prompt.append(no_newline_text)
            
            clean_text_result = re.sub(r'\*.*?\*', '', no_newline_text)
            
        translated_text = GoogleTranslator(source="auto", target="ja").translate(clean_text_result)
        embed = embed = discord.Embed(
            color=discord.Color.brand_green(),
            description=f"{no_newline_text}"
        )
        embed.add_field(name="JP ver.", value=translated_text)

        await message.channel.send(embeds=[embed])

    async with Client(base_url=BASE_URL) as client:
        audio_query = await client.create_audio_query(
            translated_text, speaker=SPEAKER_ID
        )

        with open(f"out/{message.guild.id}.wav", "wb") as f:
            f.write(await audio_query.synthesis(speaker=SPEAKER_ID))

        voice_client.play(discord.FFmpegPCMAudio(f"out/{message.guild.id}.wav"), after=lambda e: print(f'Player error: {e}') if e else None)

@bot.event
async def on_voice_state_update(member, after, before):
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if after.channel != None:
        if member.voice is None:
            if voice_client is not None and voice_client.is_connected():
                voice_client.play(discord.FFmpegPCMAudio("out/leave.wav"), after=lambda e: print(f'Player error: {e}') if e else None)
    else:
        if voice_client is not None and voice_client.is_connected():
                time.sleep(1)
                voice_client.play(discord.FFmpegPCMAudio("out/good_afternoon.wav"), after=lambda e: print(f'Player error: {e}') if e else None)

@bot.slash_command(name="roleplay-background", description="Get the background of the roleplay and the soft prompt before any conversation")
async def roleplay_background(ctx):
    embed = discord.Embed(
        title="Roleplay Background",
        color=discord.Color.green(),
        description=CHARACTER_PROMPT
    )

    await ctx.respond(embeds=[embed])

@bot.slash_command(name="join", description="Join a voice channel")
async def join(ctx):
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(ctx.author.voice.channel)
    
    vc = await ctx.author.voice.channel.connect()

    embed = discord.Embed(
        color=discord.Color.green(),
        description=f"Joined `{ctx.author.voice.channel.name}`"
    )

    await ctx.respond(embeds=[embed])

@bot.slash_command(name="speak", description="Speak")
async def speak(ctx, text: str):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is not None and voice_client.is_connected():
        async with Client(base_url=BASE_URL) as client:
            audio_query = await client.create_audio_query(
                text, speaker=SPEAKER_ID
            )

            with open(f"out/{ctx.author.voice.channel.id}.wav", "wb") as f:
                f.write(await audio_query.synthesis(speaker=SPEAKER_ID))
            
            ctx.voice_client.play(discord.FFmpegPCMAudio(f"out/{ctx.author.voice.channel.id}.wav"), after=lambda e: print(f'Player error: {e}') if e else None)

            await ctx.respond(".")
    else:
        embed = discord.Embed(
            color=discord.Color.red(),
            description="I'm not in a voice channel, to invite me to a voice channel, use the `/join` command"
        )

        await ctx.respond(embeds=[embed])

# @bot.slash_command(name="get_user_dict", description="Get user defined dictionary")
# async def get_user_dictionary(ctx, index: int = 1):
#     view = PageNav(value=index, base_url=BASE_URL)
#     async with httpx.AsyncClient() as client:
#         res = await client.get(f"{BASE_URL}/user_dict")

#         key_uuid = list(res.json().keys())[index - 1]
#         json_res = res.json()[key_uuid]

#         embed = discord.Embed(
#             title="User Defined Dictionary",
#             color=discord.Color.brand_green(),
#             description=f"**UUID:** {key_uuid}\n**Surface:** 言葉の表層形\n**Accent Type:** アクセント型（音が下がる場所を指す）\n**Priority:** 単語の優先度（0から10までの整数"
#         )

#         embed.add_field(name="Surface", value=json_res["surface"], inline=False)
#         embed.add_field(name="Pronunciation", value=json_res["pronunciation"], inline=False)
#         embed.add_field(name="Part of Speech", value=json_res["part_of_speech"])
#         embed.add_field(name="Part of Speech Detail", value=json_res["part_of_speech_detail_1"])
#         embed.add_field(name="", value="", inline=False)
#         embed.add_field(name="Priority", value=json_res["priority"])
#         embed.add_field(name="Accent Type", value=json_res["accent_type"])
#         embed.set_footer(text=f"Page: {index}/{len(res.json().keys())}")

#         await ctx.respond(embeds=[embed], view=view, delete_after=60)
        
if __name__ == "__main__":
    if BASE_URL is not None and DISCORD_TOKEN is not None and PYGMALION_URL is not None:
        bot.run(DISCORD_TOKEN)
    else:
        sys.exit(0)