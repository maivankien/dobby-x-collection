import os
import csv
import io
import re
import logging
import discord
from dotenv import load_dotenv
from discord.ext import commands
from database import (
    init_database, init_connection,
    save_x_link, get_total_links_count,
    save_user, save_server, save_channel, get_or_create_channel_id,
    get_user_links, get_latest_links, get_all_links_for_export
)

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(command_prefix='/', intents=intents)


def extract_x_links(text):
    full_url_pattern = r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[^\s]+'
    return re.findall(full_url_pattern, text)


async def handle_collect():
    total_count = await get_total_links_count()
    return f"📊 **Total X links saved: {total_count}**"


async def handle_userlinks(user):
    user_links = await get_user_links(user.id)

    if not user_links:
        return f"📭 **{user.display_name}** hasn't sent any X links yet."

    embed = discord.Embed(
        title=f"🔗 {user.display_name}'s X Links",
        color=0x1DA1F2
    )

    for i, link_data in enumerate(user_links[:10], 1):
        embed.add_field(
            name=f"{i}. {link_data['channel_name']}",
            value=f"{link_data['link_url']}\n📅 {link_data['created_at']}",
            inline=False
        )

    if len(user_links) > 10:
        embed.set_footer(text=f"Showing 10/{len(user_links)} first links")

    return embed


async def handle_latest():
    latest_links = await get_latest_links(5)

    if not latest_links:
        return "📭 No X links have been saved yet."

    embed = discord.Embed(
        title="🆕 Latest 5 X Links",
        color=0x1DA1F2
    )

    for i, link_data in enumerate(latest_links, 1):
        embed.add_field(
            name=f"{i}. {link_data['display_name']}",
            value=f"{link_data['link_url']}\n📅 {link_data['created_at']}\n📍 #{link_data['channel_name']}",
            inline=False
        )

    return embed


async def handle_export():
    all_links = await get_all_links_for_export()

    if not all_links:
        return "📭 No X links to export.", None

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Link', 'Display Name', 'Username',
                    'Channel', 'Server', 'Created At'])

    for link_data in all_links:
        writer.writerow([
            link_data['link_url'],
            link_data['display_name'],
            link_data['username'],
            link_data['channel_name'],
            link_data['server_name'],
            link_data['created_at']
        ])

    csv_content = output.getvalue()
    output.close()

    file = discord.File(io.BytesIO(csv_content.encode(
        'utf-8')), filename='x_links_export.csv')
    message = f"📁 **Exported {len(all_links)} X links to CSV file**"

    return message, file


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id
    username = message.author.name
    display_name = message.author.display_name
    channel_name = message.channel.name
    channel_id = message.channel.id
    server_name = message.guild.name if message.guild else "DM"
    server_id = message.guild.id if message.guild else 0

    try:
        await save_user(user_id, username, display_name)

        if message.guild:
            await save_server(server_id, server_name)
            await save_channel(channel_id, channel_name, server_id)

    except Exception as e:
        logger.error(f"Error saving user/server/channel to database: {e}")

    x_links = extract_x_links(message.content)
    if x_links:
        try:
            if message.guild:
                channel_id = await get_or_create_channel_id(channel_name, server_id)
            else:
                channel_id = await get_or_create_channel_id("DM", 0)
                await save_server(0, "DM")

            for link in x_links:
                await save_x_link(user_id, channel_id, link)
                logger.info(f"Saved X link: {link} from {display_name}")
        except Exception as e:
            logger.error(f"Error saving X link to database: {e}")

    await bot.process_commands(message)


@bot.command(name='collect')
async def collect(ctx):
    try:
        result = await handle_collect()
        await ctx.send(result)
    except Exception as e:
        logger.error(f"Error in collect command: {e}")
        await ctx.send("❌ An error occurred while getting statistics. Please try again later.")


@bot.command(name='userlinks')
async def userlinks(ctx, user: discord.Member):
    try:
        result = await handle_userlinks(user)
        if isinstance(result, str):
            await ctx.send(result)
        else:
            await ctx.send(embed=result)
    except Exception as e:
        logger.error(f"Error in userlinks command: {e}")
        await ctx.send("❌ An error occurred while getting user links. Please try again later.")


@bot.command(name='latest')
async def latest(ctx):
    try:
        result = await handle_latest()
        if isinstance(result, str):
            await ctx.send(result)
        else:
            await ctx.send(embed=result)
    except Exception as e:
        logger.error(f"Error in latest command: {e}")
        await ctx.send("❌ An error occurred while getting latest links. Please try again later.")


@bot.command(name='export')
async def export(ctx):
    try:
        message, file = await handle_export()
        if file:
            await ctx.send(message, file=file)
        else:
            await ctx.send(message)
    except Exception as e:
        logger.error(f"Error in export command: {e}")
        await ctx.send("❌ An error occurred while exporting file. Please try again later.")


@bot.event
async def on_ready():
    await init_connection()
    await init_database()

    logger.info(f'{bot.user} has connected to Discord!')
    print(f'{bot.user} is ready!')
    print("✅ Available prefix commands:")
    print("  - /collect")
    print("  - /userlinks @username")
    print("  - /latest")
    print("  - /export")


logger.info("Starting Discord bot...")
bot.run(DISCORD_TOKEN)
