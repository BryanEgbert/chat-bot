import discord
import httpx

class PageNav(discord.ui.View):
    def __init__(self, value: int, base_url: str):
        super().__init__()
        self.value = value
        self.base_url = base_url

    @discord.ui.button(label='<', style=discord.ButtonStyle.primary)
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}/user_dict")
            
            keys_list = list(res.json().keys())
            if self.value <= 1:
                self.value = len(keys_list)
            else:
                self.value -= 1

            key_uuid = keys_list[self.value - 1]
            json_res = res.json()[key_uuid]

            embed = discord.Embed(
                title="User Defined Dictionary",
                color=discord.Color.brand_green(),
                description=f"**UUID:** {key_uuid}\n**Surface:** 言葉の表層形\n**Accent Type:** アクセント型（音が下がる場所を指す）\n**Priority:** 単語の優先度（0から10までの整数"
            )

            embed.add_field(name="Surface", value=json_res["surface"], inline=False)
            embed.add_field(name="Pronounciation", value=json_res["pronunciation"], inline=False)
            embed.add_field(name="Part of Speech", value=json_res["part_of_speech"])
            embed.add_field(name="Part of Speech Detail", value=json_res["part_of_speech_detail_1"])
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name="Priority", value=json_res["priority"])
            embed.add_field(name="Accent Type", value=json_res["accent_type"])
            embed.set_footer(text=f"Page: {self.value}/{len(res.json().keys())}")

            await interaction.response.edit_message(embeds=[embed], view=self, delete_after=60)
    
    @discord.ui.button(label='>', style=discord.ButtonStyle.blurple)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}/user_dict")
            
            keys_list = list(res.json().keys())
            if self.value >= len(keys_list):
                self.value = 1
            else:
                self.value += 1

            key_uuid = keys_list[self.value - 1]
            json_res = res.json()[key_uuid]

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
            embed.set_footer(text=f"Page: {self.value}/{len(res.json().keys())}")

            await interaction.response.edit_message(embeds=[embed], view=self, delete_after=60)