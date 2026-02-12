import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
VOICE_CHANNEL_ID = os.getenv('VOICE_CHANNEL_ID')

# Path ke file audio welcome
WELCOME_SOUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'welcome.mp3')

# Setup bot dengan intents yang diperlukan
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Lock untuk mencegah audio overlap
audio_lock = asyncio.Lock()


@bot.event
async def on_ready():
    """Event ketika bot berhasil login dan siap."""
    print(f'✅ Bot {bot.user.name} sudah online!')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'🔊 File audio: {WELCOME_SOUND}')
    print('-----------------------------------')

    # Auto-join voice channel jika VOICE_CHANNEL_ID diset
    if VOICE_CHANNEL_ID:
        channel = bot.get_channel(int(VOICE_CHANNEL_ID))
        if channel and isinstance(channel, discord.VoiceChannel):
            try:
                await channel.connect(self_deaf=True)
                print(f'🎤 Auto-join ke voice channel: {channel.name}')
            except Exception as e:
                print(f'❌ Gagal auto-join: {e}')
        else:
            print(f'⚠️ Voice channel dengan ID {VOICE_CHANNEL_ID} tidak ditemukan.')


@bot.event
async def on_voice_state_update(member, before, after):
    """Deteksi pengguna masuk/keluar voice channel."""

    # Abaikan jika yang join adalah bot sendiri
    if member.bot:
        return

    # Cek apakah user BARU MASUK ke voice channel (sebelumnya tidak di channel / pindah channel)
    if after.channel is not None and (before.channel is None or before.channel != after.channel):
        # Cek apakah bot ada di voice channel yang sama
        guild = member.guild
        voice_client = guild.voice_client

        if voice_client and voice_client.is_connected() and voice_client.channel == after.channel:
            print(f'👋 {member.display_name} masuk ke {after.channel.name} - Memutar welcome sound...')
            await play_welcome_sound(voice_client)


async def play_welcome_sound(voice_client):
    """Putar file audio welcome.mp3."""
    async with audio_lock:
        try:
            # Tunggu jika sedang memutar audio lain
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.5)

            # Putar audio menggunakan FFmpeg
            audio_source = discord.FFmpegPCMAudio(
                WELCOME_SOUND,
                executable='ffmpeg'
            )

            # Atur volume (0.0 - 2.0, default 1.0)
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=1.0)

            voice_client.play(audio_source)
            print(f'🔊 Memutar welcome sound...')

            # Tunggu sampai audio selesai
            while voice_client.is_playing():
                await asyncio.sleep(0.5)

            print(f'✅ Welcome sound selesai diputar.')

        except Exception as e:
            print(f'❌ Error memutar audio: {e}')


@bot.command(name='join')
async def join_voice(ctx):
    """Command !join - Bot masuk ke voice channel user."""

    # Cek apakah user ada di voice channel
    if ctx.author.voice is None:
        await ctx.send('❌ Kamu harus berada di voice channel terlebih dahulu!')
        return

    channel = ctx.author.voice.channel

    # Cek apakah bot sudah di voice channel
    if ctx.voice_client is not None:
        if ctx.voice_client.channel == channel:
            await ctx.send(f'✅ Bot sudah berada di **{channel.name}**')
            return
        # Pindah ke channel baru
        await ctx.voice_client.move_to(channel)
        await ctx.send(f'🔄 Bot pindah ke **{channel.name}**')
    else:
        # Join voice channel
        await channel.connect(self_deaf=True)
        await ctx.send(f'🎤 Bot bergabung ke **{channel.name}**! Bot akan stay 24/7 dan menyambut setiap pengguna baru.')


@bot.command(name='leave')
async def leave_voice(ctx):
    """Command !leave - Bot keluar dari voice channel."""

    if ctx.voice_client is not None:
        channel_name = ctx.voice_client.channel.name
        await ctx.voice_client.disconnect()
        await ctx.send(f'👋 Bot keluar dari **{channel_name}**')
    else:
        await ctx.send('❌ Bot tidak sedang berada di voice channel.')


@bot.command(name='setchannel')
async def set_channel(ctx, channel_id: str = None):
    """Command !setchannel <id> - Set voice channel untuk auto-join."""

    if channel_id is None:
        await ctx.send(
            '📌 **Cara penggunaan:** `!setchannel <voice_channel_id>`\n'
            '💡 Aktifkan Developer Mode di Settings → Advanced, '
            'lalu klik kanan voice channel → Copy Channel ID'
        )
        return

    channel = bot.get_channel(int(channel_id))
    if channel and isinstance(channel, discord.VoiceChannel):
        # Update .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        with open(env_path, 'r') as f:
            lines = f.readlines()

        with open(env_path, 'w') as f:
            found = False
            for line in lines:
                if line.startswith('VOICE_CHANNEL_ID'):
                    f.write(f'VOICE_CHANNEL_ID={channel_id}\n')
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f'VOICE_CHANNEL_ID={channel_id}\n')

        # Join channel sekarang
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect(self_deaf=True)

        await ctx.send(
            f'✅ Voice channel diset ke **{channel.name}** (ID: {channel_id})\n'
            f'🎤 Bot akan auto-join channel ini setiap kali restart.'
        )
    else:
        await ctx.send(f'❌ Channel dengan ID `{channel_id}` tidak ditemukan atau bukan voice channel.')


@bot.command(name='status')
async def bot_status(ctx):
    """Command !status - Cek status bot."""

    if ctx.voice_client and ctx.voice_client.is_connected():
        channel = ctx.voice_client.channel
        members = [m.display_name for m in channel.members if not m.bot]
        member_list = ', '.join(members) if members else 'Tidak ada'

        embed = discord.Embed(
            title='🤖 Status Bot Welcome',
            color=discord.Color.green()
        )
        embed.add_field(name='🔊 Voice Channel', value=channel.name, inline=False)
        embed.add_field(name='👥 Member di Channel', value=member_list, inline=False)
        embed.add_field(name='🎵 Audio File', value='welcome.mp3 ✅' if os.path.exists(WELCOME_SOUND) else 'welcome.mp3 ❌', inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send('🔇 Bot tidak terhubung ke voice channel. Gunakan `!join` untuk bergabung.')


@bot.command(name='help_welcome')
async def help_command(ctx):
    """Command !help_welcome - Tampilkan daftar command."""

    embed = discord.Embed(
        title='📖 Daftar Command Bot Welcome',
        description='Berikut adalah command yang tersedia:',
        color=discord.Color.blue()
    )
    embed.add_field(name='!join', value='Bot masuk ke voice channel kamu', inline=False)
    embed.add_field(name='!leave', value='Bot keluar dari voice channel', inline=False)
    embed.add_field(name='!setchannel <id>', value='Set voice channel untuk auto-join saat bot restart', inline=False)
    embed.add_field(name='!status', value='Cek status bot dan voice channel', inline=False)
    embed.add_field(name='!help_welcome', value='Tampilkan daftar command ini', inline=False)
    await ctx.send(embed=embed)


# Handle reconnect jika bot terputus
@bot.event
async def on_disconnect():
    print('⚠️ Bot terputus dari Discord. Mencoba reconnect...')


# Jalankan bot
if __name__ == '__main__':
    if not TOKEN:
        print('❌ DISCORD_TOKEN tidak ditemukan di .env file!')
        print('   Silakan isi token di file .env')
    else:
        print('🚀 Memulai bot...')
        bot.run(TOKEN)
