import asyncio
import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View, button

name_changes = {}

class PrivateRoomsView(View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @button(label="Close access", style=nextcord.ButtonStyle.gray)
    async def close_channel(self, button: Button, interaction: nextcord.Interaction):
        user = interaction.user

        if user.voice and user.voice.channel:
            voice_channel = user.voice.channel
            overwrites = voice_channel.overwrites or {}
            role = interaction.guild.default_role
            overwrites[role] = nextcord.PermissionOverwrite(view_channel=False, connect=False)
            await voice_channel.edit(overwrites=overwrites)
            await interaction.response.send_message(f"Voice channel access '{voice_channel.name}' closed.")
        else:
            await interaction.response.send_message("You must be in a voice channel to block his access.")

    @button(label="Change name", style=nextcord.ButtonStyle.gray)
    async def change_name(self, button: Button, interaction: nextcord.Interaction):
        user = interaction.user

        if user.voice and user.voice.channel:
            voice_channel = user.voice.channel

            await interaction.response.send_message("Enter a new name for the room.")

            def check(m):
                return m.author == user and m.channel == voice_channel

            try:
                response = await self.bot.wait_for('message', check=check, timeout=60)
                new_name = response.content

                await voice_channel.edit(name=new_name)
                await interaction.response.send_message(f"Voice channel name changed to: {new_name}")
            except asyncio.TimeoutError:
                await interaction.response.send_message("The timeout has expired, please try again.")
        else:
            await interaction.response.send_message("You must be in a voice channel to change its name.")

    @button(label="To open access", style=nextcord.ButtonStyle.gray)
    async def open_channel(self, button: Button, interaction: nextcord.Interaction):
        user = interaction.user

        if user.voice and user.voice.channel:
            voice_channel = user.voice.channel
            overwrites = voice_channel.overwrites or {}
            role = interaction.guild.default_role
            overwrites[role] = nextcord.PermissionOverwrite(view_channel=True, connect=True)
            await voice_channel.edit(overwrites=overwrites)
            await interaction.response.send_message(f"Voice channel access '{voice_channel.name}' open.")
        else:
            await interaction.response.send_message("You must be in a voice channel to enable it.")


class PrivateRooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def private_rooms(self, ctx):
        """
        `.private_rooms`
        """
        category = await ctx.guild.create_category('Private rooms')
        text_channel = await ctx.guild.create_text_channel('private-rooms-leafy', category=category)
        voice_channel = await ctx.guild.create_voice_channel('create-voice-channel', category=category)

        embed = nextcord.Embed(title='Private rooms', description='Welcome to private rooms!', color=0x2b2d31)
        embed.add_field(name='Close access', value="<:882630044944576532:1153745875554795551>", inline=False)
        embed.add_field(name='Change name', value="<:882630048190967859:1172186424632692927>", inline=False)
        embed.add_field(name='To open access', value="<:882630044550324274:1172186389207588894>", inline=False)

        message = await text_channel.send(embed=embed, view=PrivateRoomsView(self.bot))
        await ctx.send('Private rooms have been successfully created!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.name == 'create-voice-channel':
            channel_name = f'{member.display_name}\'s Room'
            category = after.channel.category
            new_voice_channel = await category.create_voice_channel(channel_name)
            await member.move_to(new_voice_channel)
        if before.channel and before.channel.name != 'create-voice-channel' and not before.channel.members:
            await before.channel.delete()

        # Применение запрошенных изменений названия, если пользователь находится в голосовом канале
        if member.voice and member.id in name_changes:
            new_name = name_changes[member.id]
            await member.voice.channel.edit(name=new_name)
            del name_changes[member.id]

def setup(bot):
    bot.add_cog(PrivateRooms(bot))
