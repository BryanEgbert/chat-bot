from voicevox import Client
import asyncio
import discord
import os
import time
import sys
import httpx
from discord.ext import commands
from views.page_nav import PageNav

BASE_URL = os.environ.get("VOICEVOX_URL")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=';', description="JP bot", intents=intents)

@bot.command()
async def join(ctx):
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(ctx.author.voice.channel)
    
    await ctx.author.voice.channel.connect()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def setup_hook():
    async with Client(base_url=BASE_URL) as client:
        audio_query = await client.create_audio_query(
            "こんにちは。", speaker=20
        )

        with open(f"out/good_afternoon.wav", "wb") as f:
            f.write(await audio_query.synthesis(speaker=20))

        audio_query = await client.create_audio_query("プレーヤーが音声通話を終了しました", speaker=20)
        with open(f"out/leave.wav", "wb") as f:
            f.write(await audio_query.synthesis(speaker=20))

@bot.event
async def on_voice_state_update(member, after, before):
    print(f"member: {member.voice} after: {after}")
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if after.channel != None:
        print(voice_client)
        if member.voice is None:
            if voice_client is not None and voice_client.is_connected():
                voice_client.play(discord.FFmpegPCMAudio("out/leave.wav"), after=lambda e: print(f'Player error: {e}') if e else None)
    else:
        if voice_client is not None and voice_client.is_connected():
                time.sleep(1)
                voice_client.play(discord.FFmpegPCMAudio("out/good_afternoon.wav"), after=lambda e: print(f'Player error: {e}') if e else None)


@bot.command()
async def speak(ctx, text: str):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is not None and voice_client.is_connected():
        async with Client(base_url=BASE_URL) as client:
            audio_query = await client.create_audio_query(
                text, speaker=20
            )

            with open(f"out/{ctx.author.voice.channel.id}.wav", "wb") as f:
                f.write(await audio_query.synthesis(speaker=20))
            
            ctx.voice_client.play(discord.FFmpegPCMAudio(f"out/{ctx.author.voice.channel.id}.wav"), after=lambda e: print(f'Player error: {e}') if e else None)
    else:
        await ctx.send("I'm not in a voice channel, to invite me to a voice channel, use the `;join` command")

@bot.command()
async def get_user_dictionary(ctx, index: int = 1):
    view = PageNav(value=index, base_url=BASE_URL)
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BASE_URL}/user_dict")

        key_uuid = list(res.json().keys())[index - 1]
        json_res = res.json()[key_uuid]

        # for key in res.json()[key_uuid]:
        embed = discord.Embed(
            title="User Defined Dictionary",
            color=discord.Color.brand_green(),
            description=f"**UUID:** {key_uuid}\n**Surface:** 言葉の表層形\n**Accent Type:** アクセント型（音が下がる場所を指す）\n**Priority:** 単語の優先度（0から10までの整数"
        )

        embed.add_field(name="Surface", value=json_res["surface"], inline=False)
        embed.add_field(name="Pronunciation", value=json_res["pronunciation"], inline=False)
        embed.add_field(name="Part of Speech", value=json_res["part_of_speech"])
        embed.add_field(name="Part of Speech Detail", value=json_res["part_of_speech_detail_1"])
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="Priority", value=json_res["priority"])
        embed.add_field(name="Accent Type", value=json_res["accent_type"])
        embed.set_footer(text=f"Page: {index}/{len(res.json().keys())}")

        await ctx.send(embeds=[embed], view=view, delete_after=60)
if __name__ == "__main__":
    if BASE_URL is not None:
        bot.run("MTEzNTQ0NjY5NzQyMjYxODYzNg.GqTMEa.OjFe-OvwVkZOKuuz6yiZNLfanGHX5HVtnafIgw")
    else:
        sys.exit(0)