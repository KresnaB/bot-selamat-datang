import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from gtts import gTTS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('welcome.bot')

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
    logger.info(f'✅ Bot {bot.user.name} sudah online!')
    logger.info(f'🆔 Bot ID: {bot.user.id}')
    logger.info(f'🔊 File audio: {WELCOME_SOUND}')
    print('-----------------------------------')

    # Start keep_alive loop
    if not keep_alive.is_running():
        keep_alive.start()

    # Auto-join voice channel jika VOICE_CHANNEL_ID diset
    await check_and_join_voice()


async def check_and_join_voice():
    """Helper function to join voice channel safely."""
    if not VOICE_CHANNEL_ID:
        return

    try:
        channel = bot.get_channel(int(VOICE_CHANNEL_ID))
        if channel and isinstance(channel, discord.VoiceChannel):
            if bot.voice_clients:
                # Already connected?
                vc = bot.voice_clients[0]
                if vc.channel.id == channel.id and vc.is_connected():
                    return # Already in correct channel
                
                # In wrong channel or disconnected state
                await vc.disconnect(force=True)
                await asyncio.sleep(1)

            await channel.connect(self_deaf=True)
            logger.info(f'🎤 Auto-join ke voice channel: {channel.name}')
        else:
            logger.warning(f'⚠️ Voice channel dengan ID {VOICE_CHANNEL_ID} tidak ditemukan.')
    except Exception as e:
        logger.error(f'❌ Gagal auto-join: {e}')


@bot.event
async def on_voice_state_update(member, before, after):
    """Deteksi pengguna masuk/keluar voice channel."""

    # 1. Handle Bot Reconnection (Self)
    if member.id == bot.user.id:
        if before.channel is not None and after.channel is None:
            # Bot disconnected
            logger.warning("⚠️ Bot terputus dari voice channel (on_voice_state_update).")
            # Keep-alive loop will handle reconnection
        return

    if member.bot:
        return

    # 2. Cek apakah user BARU MASUK ke voice channel
    if after.channel is not None and (before.channel is None or before.channel != after.channel):
        # Cek apakah bot ada di voice channel yang sama
        guild = member.guild
        voice_client = guild.voice_client

        if voice_client and voice_client.is_connected() and voice_client.channel == after.channel:
            logger.info(f'👋 {member.display_name} masuk ke {after.channel.name} - Memutar welcome sound...')
            await asyncio.sleep(1) # Delay 1 detik sebelum memutar suara
            await play_welcome_sound(voice_client, member.display_name)


@tasks.loop(minutes=1)
async def keep_alive():
    """Loop untuk menjaga koneksi bot tetap hidup."""
    if not VOICE_CHANNEL_ID:
        return

    try:
        channel = bot.get_channel(int(VOICE_CHANNEL_ID))
        if not channel:
            return

        # Check existing connection
        voice_client = channel.guild.voice_client
        
        if voice_client and voice_client.is_connected():
            if voice_client.channel.id != channel.id:
                # Wrong channel
                logger.info("🔄 Keep-alive: Bot in wrong channel, moving...")
                await voice_client.move_to(channel)
        else:
            # Not connected or disconnected
            logger.info('🔄 Keep-alive: Bot terputus, mencoba reconnect...')
            if voice_client:
                try:
                    await voice_client.disconnect(force=True)
                except Exception:
                    pass
                await asyncio.sleep(1)
            
            await check_and_join_voice()

    except Exception as e:
        logger.error(f'❌ Keep-alive error: {e}')

@keep_alive.before_loop
async def before_keep_alive():
    await bot.wait_until_ready()

async def play_welcome_sound(voice_client, member_name):
    """Putar file audio welcome custom menggunakan TTS dengan retry logic."""
    async with audio_lock:
        try:
            # Tunggu jika sedang memutar audio lain
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.5)

            # Generate TTS text
            text = f"Welcome to the stream {member_name}"
            
            # Temporary filename
            filename = f"welcome_{member_name}.mp3"
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

            # Generate audio using gTTS with retry
            for attempt in range(3):
                try:
                    # Run in executor to avoid blocking
                    await bot.loop.run_in_executor(None, lambda: gTTS(text=text, lang='id').save(file_path))
                    break
                except Exception as e:
                    if attempt == 2:
                        logger.error(f"❌ Gagal generate TTS setelah 3 percobaan: {e}")
                        return
                    logger.warning(f"⚠️ Gagal generate TTS (percobaan {attempt+1}), retry... {e}")
                    await asyncio.sleep(2)

            # Putar audio menggunakan FFmpeg
            if os.path.exists(file_path):
                try:
                    audio_source = discord.FFmpegPCMAudio(file_path, executable='ffmpeg')
                    audio_source = discord.PCMVolumeTransformer(audio_source, volume=1.0)
                    
                    voice_client.play(audio_source)
                    logger.info(f'🔊 Memutar welcome sound untuk {member_name}...')

                    # Tunggu sampai audio selesai
                    while voice_client.is_playing():
                        await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"❌ Error playing audio: {e}")
                finally:
                    # Clean up file after playing
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"⚠️ Gagal menghapus file temporary: {e}")
            
            logger.info(f'✅ Welcome sound selesai.')

        except Exception as e:
            logger.error(f'❌ Critical Error memutar audio: {e}')


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

    try:
        channel = bot.get_channel(int(channel_id))
        if channel and isinstance(channel, discord.VoiceChannel):
            # Update .env file
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            with open(env_path, 'r') as f:
                lines = f.readlines()

            found = False
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('VOICE_CHANNEL_ID'):
                        f.write(f'VOICE_CHANNEL_ID={channel_id}\n')
                        found = True
                    else:
                        f.write(line)
                if not found:
                    f.write(f'\nVOICE_CHANNEL_ID={channel_id}\n')

            # Update global var
            global VOICE_CHANNEL_ID
            VOICE_CHANNEL_ID = channel_id

            # Join channel sekarang
            if ctx.voice_client:
                if ctx.voice_client.channel.id != channel.id:
                    await ctx.voice_client.move_to(channel)
            else:
                await channel.connect(self_deaf=True)

            await ctx.send(
                f'✅ Voice channel diset ke **{channel.name}** (ID: {channel_id})\n'
                f'🎤 Bot akan auto-join channel ini setiap kali restart.'
            )
        else:
            await ctx.send(f'❌ Channel dengan ID `{channel_id}` tidak ditemukan atau bukan voice channel.')
    except ValueError:
        await ctx.send('❌ ID Channel harus berupa angka.')


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
    embed.add_field(name='!reconnect', value='Paksa reset koneksi bot dan join ulang', inline=False)
    embed.add_field(name='!status', value='Cek status bot dan voice channel', inline=False)
    embed.add_field(name='!help_welcome', value='Tampilkan daftar command ini', inline=False)
    await ctx.send(embed=embed)


@bot.command(name='reconnect')
async def reconnect(ctx):
    """Command !reconnect - Paksa bot untuk disconnect dan connect ulang."""
    logger.info(f"Manual reconnect requested by {ctx.author}")
    
    # 1. Force Disconnect
    if ctx.voice_client:
        try:
            await ctx.voice_client.disconnect(force=True)
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Error disconnecting: {e}")

    # 2. Reconnect
    target_channel = None
    if ctx.author.voice and ctx.author.voice.channel:
        target_channel = ctx.author.voice.channel
    elif VOICE_CHANNEL_ID:
        target_channel = bot.get_channel(int(VOICE_CHANNEL_ID))

    if target_channel:
        try:
            await target_channel.connect(self_deaf=True)
            await ctx.send(f'✅ Berhasil reconnect ke **{target_channel.name}**')
        except Exception as e:
            await ctx.send(f'❌ Gagal reconnect: {e}')
    else:
        await ctx.send('❌ Tidak ada channel tujuan. Gunakan !join.')


# Handle reconnect jika bot terputus
@bot.event
async def on_disconnect():
    logger.warning('⚠️ Bot terputus dari Discord. Mencoba reconnect...')


# Jalankan bot
if __name__ == '__main__':
    if not TOKEN:
        print('❌ DISCORD_TOKEN tidak ditemukan di .env file!')
        print('   Silakan isi token di file .env')
    else:
        print('🚀 Memulai bot...')
        bot.run(TOKEN)
