import discord
from discord.ext import commands, tasks
import sqlite3
from datetime import datetime, timedelta


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Role parameters 
role_1_id = 1017154265426427966
role_2_id = 962693218338754560
role_nato_id = 953235730463850506
role_russia_id = 953235676403486720
administrator_role_id = 971102625040855070  #  administrator role ID

# конект к бд офицеров
conn_officers = sqlite3.connect('officers.db')
cursor_officers = conn_officers.cursor()

# создание базы
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

# блеклист
conn_blacklist = sqlite3.connect('blacklist.db')
cursor_blacklist = conn_blacklist.cursor()

# создать блеклист
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
async def add(ctx, officer: discord.Member, steamid, position, side):
    date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    added_by = f'{ctx.author.name}#{ctx.author.discriminator}'

    # доп информация
    cursor_officers.execute('''
        INSERT INTO officers (nickname, steamid, position, side, date_added, added_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (officer.display_name, steamid, position, side, date_added, added_by))
    conn_officers.commit()

    # ролиr
    role_1 = ctx.guild.get_role(role_1_id)
    role_2 = ctx.guild.get_role(role_2_id)
    role_nato = ctx.guild.get_role(role_nato_id)
    role_russia = ctx.guild.get_role(role_russia_id)

    if role_1:
        await officer.add_roles(role_1)

    if role_2:
        await officer.add_roles(role_2)

    if side.lower() == 'nato':
        if role_nato:
            await officer.add_roles(role_nato, reason="NATO side assigned.")
    elif side.lower() == 'russia':
        if role_russia:
            await officer.add_roles(role_russia, reason="Russia side assigned.")

    # вывод
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
async def officers(ctx):
    # вывести список офицеров
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
        # форматирование
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
async def remove(ctx, officer: discord.Member):

    cursor_officers.execute('SELECT * FROM officers WHERE nickname = ?', (officer.display_name,))
    officer_info = cursor_officers.fetchone()

    if officer_info:
        # удалить офицера
        cursor_officers.execute('DELETE FROM officers WHERE nickname = ?', (officer.display_name,))
        conn_officers.commit()

        # снять роли с офицера
        role_1 = ctx.guild.get_role(role_1_id)
        role_2 = ctx.guild.get_role(role_2_id)
        role_nato = ctx.guild.get_role(role_nato_id)
        role_russia = ctx.guild.get_role(role_russia_id)

        if role_1:
            await officer.remove_roles(role_1)

        if role_2:
            await officer.remove_roles(role_2)

         # Знімання додаткових ролей в залежності від значення side
        if officer_info[4].lower() == 'nato':
            if role_nato:
                await officer.remove_roles(role_nato, reason="NATO side removed.")
        elif officer_info[4].lower() == 'russia':
            if role_russia:
                await officer.remove_roles(role_russia, reason="Russia side removed.")

        # 14 дней удаление
        date_added = datetime.strptime(officer_info[5], '%Y-%m-%d %H:%M:%S')
        if datetime.now() - date_added < timedelta(days=14):
            # добавить в блеклист
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
async def blacklist(ctx):
    # вывести блеклист
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
        # вывод информация
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
    embed.add_field(name='!add <officer> <steamid> <пост> <nato/russia>', value='Добавляет нового офицера', inline=False)
    embed.add_field(name='!officers', value='Показывает список офицеров.', inline=False)
    embed.add_field(name='!remove <officer>', value='Удаляет офицера из базы данных и удаляет его роли', inline=False)
    embed.add_field(name='!blacklist', value='Показывает ЧС Офицеров', inline=False)
    await ctx.send(embed=embed)

bot.run('secret')
