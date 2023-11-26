import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Role parameters (replace with your role IDs)
role_1_id = 1178069995582918686
role_2_id = 1178070027560292506
administrator_role_id = 1178075204820418610  # Replace with your administrator role ID

# Connect to the main officers database
conn_officers = sqlite3.connect('officers.db')
cursor_officers = conn_officers.cursor()

# Create the officers table if it doesn't exist
cursor_officers.execute('''
    CREATE TABLE IF NOT EXISTS officers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        steamid TEXT,
        position TEXT,
        side TEXT,
        date_added TEXT,
        added_by TEXT
    )
''')
conn_officers.commit()

# Connect to the blacklist database
conn_blacklist = sqlite3.connect('blacklist.db')
cursor_blacklist = conn_blacklist.cursor()

# Create the blacklist table if it doesn't exist
cursor_blacklist.execute('''
    CREATE TABLE IF NOT EXISTS blacklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT,
        steamid TEXT,
        position TEXT,
        side TEXT,
        date_removed TEXT,
        removed_by TEXT
    )
''')
conn_blacklist.commit()

@bot.event
async def on_ready():
    print(f'Bot is ready: {bot.user.name}')

@bot.command()
@commands.has_role(administrator_role_id)
async def add_officer(ctx, officer: discord.Member, steamid, position, side):
    date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    added_by = f'{ctx.author.name}#{ctx.author.discriminator}'

    # Add information to the officers database
    cursor_officers.execute('''
        INSERT INTO officers (nickname, steamid, position, side, date_added, added_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (officer.display_name, steamid, position, side, date_added, added_by))
    conn_officers.commit()

    # Add roles to the user
    role_1 = ctx.guild.get_role(role_1_id)
    role_2 = ctx.guild.get_role(role_2_id)

    if role_1:
        await officer.add_roles(role_1)

    if role_2:
        await officer.add_roles(role_2)

    # Output information in the form of an embed
    embed = discord.Embed(
        title=f'Officer {officer.display_name} added!',
        color=discord.Color.green()
    )
    embed.add_field(name='SteamID', value=steamid, inline=False)
    embed.add_field(name='Position', value=position, inline=False)
    embed.add_field(name='Side', value=side, inline=False)
    embed.add_field(name='Added by', value=added_by, inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(administrator_role_id)
async def list_officers(ctx):
    # Retrieve all officers from the officers database
    cursor_officers.execute('SELECT * FROM officers')
    officers = cursor_officers.fetchall()

    if not officers:
        embed = discord.Embed(
            title='List of Officers',
            description='There are no officers in the database.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        # Format and output information about officers
        embed = discord.Embed(
            title='List of Officers',
            color=discord.Color.blue()
        )
        for officer in officers:
            embed.add_field(
                name=f'{officer[1]} (ID: {officer[0]})',
                value=f'SteamID: {officer[2]}\nPosition: {officer[3]}\nSide: {officer[4]}\nAdded by: {officer[6]}\nDate Added: {officer[5]}',
                inline=False
            )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_role(administrator_role_id)
async def remove_officer(ctx, officer: discord.Member):
    # Check if an officer with the specified ID exists
    cursor_officers.execute('SELECT * FROM officers WHERE nickname = ?', (officer.display_name,))
    officer_info = cursor_officers.fetchone()

    if officer_info:
        # Remove the officer from the database
        cursor_officers.execute('DELETE FROM officers WHERE nickname = ?', (officer.display_name,))
        conn_officers.commit()

        # Remove roles from the user
        role_1 = ctx.guild.get_role(role_1_id)
        role_2 = ctx.guild.get_role(role_2_id)

        if role_1:
            await officer.remove_roles(role_1)

        if role_2:
            await officer.remove_roles(role_2)

        # Check if the officer was added less than 14 days ago
        date_added = datetime.strptime(officer_info[5], '%Y-%m-%d %H:%M:%S')
        if datetime.now() - date_added < timedelta(days=14):
            # Add the officer to the blacklist
            cursor_blacklist.execute('''
                INSERT INTO blacklist (nickname, steamid, position, side, date_removed, removed_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (officer_info[1], officer_info[2], officer_info[3], officer_info[4], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f'{ctx.author.name}#{ctx.author.discriminator}'))
            conn_blacklist.commit()

        embed = discord.Embed(
            title=f'Officer {officer.display_name} removed.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title=f'Officer {officer.display_name} not found.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_role(administrator_role_id)
async def list_blacklist(ctx):
    # Retrieve blacklisted officers from the blacklist database
    cursor_blacklist.execute('SELECT * FROM blacklist')
    blacklisted_officers = cursor_blacklist.fetchall()

    if not blacklisted_officers:
        embed = discord.Embed(
            title='Blacklisted Officers',
            description='There are no officers in the blacklist.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        # Format and output information about blacklisted officers
        embed = discord.Embed(
            title='Blacklisted Officers',
            color=discord.Color.red()
        )
        for officer in blacklisted_officers:
            embed.add_field(
                name=f'{officer[1]} (ID: {officer[0]})',
                value=f'SteamID: {officer[2]}\nPosition: {officer[3]}\nSide: {officer[4]}\nRemoved by: {officer[6]}\nDate Removed: {officer[5]}',
                inline=False
            )
        await ctx.send(embed=embed)

@bot.command()
async def bot_help(ctx):
    embed = discord.Embed(
        title='Help Information',
        description='List of available commands:',
        color=discord.Color.gold()
    )
    embed.add_field(name='!add_officer <officer> <steamid> <position> <side>', value='Adds a new officer to the database and assigns roles.', inline=False)
    embed.add_field(name='!list_officers', value='Shows a list of all officers in the database.', inline=False)
    embed.add_field(name='!remove_officer <officer>', value='Removes an officer by their ID and removes roles.', inline=False)
    embed.add_field(name='!list_blacklist', value='Shows a list of all blacklisted officers.', inline=False)
    await ctx.send(embed=embed)


bot.run('YOUR_TOKEN_BOT')
