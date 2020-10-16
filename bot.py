import hashlib
import os

import discord
from discord.ext import commands, tasks
from logzero import logger as log

import cw_mongo as cw_db
from codewarse_api import api as cw

TOKEN = os.environ.get('TOKEN')
client = commands.Bot(command_prefix='ex/')


@client.event
async def on_ready():
    auto_update_cw_profiles.start()
    custom = discord.Game(name="ex/codewars")
    await client.change_presence(status=discord.Status.online, activity=custom)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Неверно указаны аргументы!\nВведите:`ex/help {ctx.command.name}` ")
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Такой команды не существует!\nЧтобы просмотреть список команд введите: `ex/help`')


@client.command()
async def check(ctx, username):
    # получаем код для валидации аккаунта в виде md5 из discord id
    code = hashlib.md5(str(ctx.author.id).encode()).hexdigest()

    # проверки аккаунта
    log.debug(f'{ctx.command.name}'
              f'\n{ctx.message}\n'
              f'\tActivation Code: [{code}]\n'
              f'\tActivation check: {cw.activation_check(username, code)}\n'
              f'\tDuplicate check: {cw_db.abuse_check(ctx.author.id)}')
    if not cw.activation_check(username, code):
        return await ctx.send('Указан не верный код активации либо указаный аккаунт не существует')
    if not cw_db.abuse_check(ctx.author.id):
        return await ctx.send('Данный аккаунт уже привязан')

    # Ммм, хардкод :clown:
    log.debug("Try get server obj")
    guild = client.get_guild(int(os.getenv("SERVER_ID")))  # extremecode discord server
    log.debug(f"{guild.name}")
    roles = {
        't0': guild.get_role(int(os.getenv("TIER0"))),
        't1': guild.get_role(int(os.getenv("TIER1"))),
        't2': guild.get_role(int(os.getenv("TIER2")))
    }  # получаем роли сервера

    # cw.get_rank возвращает число ранка. В кодварсе оно отрицательно ибо в будущем будут добавлены dan ранки
    rank = cw.get_rank(username)
    tier_dict = {
        -8: [roles['t0']],
        -7: [roles['t0']],
        -6: [roles['t0'], roles['t1']],
        -5: [roles['t0'], roles['t1']],
        -4: [roles['t0'], roles['t1'], roles['t2']],
        -3: [roles['t0'], roles['t1'], roles['t2']],
        -2: [roles['t0'], roles['t1'], roles['t2']],
        -1: [roles['t0'], roles['t1'], roles['t2']],
        # Когда будет tier 3!
    }
    # выдача ролей
    member = guild.get_member(ctx.author.id)
    for role in tier_dict[int(rank)]:
        await member.add_roles(role, reason=f'{ctx.author.name} with Rank: {rank}')
    cw_db.insert_cw_profile(username, ctx.author.id)
    # await ctx.send('Поздровляю, вы теперь не лох!')
    await ctx.send('Проверка успешно пройдена!')


@client.command(aliases=['cw'])
async def codewars(ctx):
    await ctx.author.send(content=f'''
  Привет! Сейчас мы интегрируем твой профиль CodeWars
  1. Зайди в настройки профиля: https://www.codewars.com/users/edit
  2. Введи в поле Clan следующий код активации: `{hashlib.md5(str(ctx.author.id).encode()).hexdigest()}`
  3. Скопируй свой Username
  4. Сохрани профиль
  5. Отправь сюда свой Username в следующем формате ex/check Username
  6. PROFIT
  7. ???
''', )


@client.command()
async def send_top(ctx, amount=10):
    log.info(f'{ctx.author.name}: {ctx.message.content}')
    log.debug(f'{ctx.author.id}|{ctx.author.name} \n'
              f'{ctx.message}')
    profiles = cw_db.get_top_rank(int(amount if amount < 20 else 20))  # в дискорде ограничение по количеству полей
    embed = discord.Embed(colour=discord.Colour(0x7b03b9), )

    embed.set_author(name=f"Top {amount if amount < 20 else 20}")
    embed.add_field(name="RANK", value="\u200B", inline=True)
    embed.add_field(name="Codewars", value="\u200B", inline=True)
    embed.add_field(name="Discord", value="\u200B", inline=True)
    for profile in profiles:
        embed.add_field(name="⸻⸻⸻", value=f"{profile['ranks']['overall']['name']}", inline=True)
        embed.add_field(name="⸻⸻⸻", value=f"{profile['username']}", inline=True)
        embed.add_field(name="⸻⸻⸻", value=f"<@{profile['discord_id']}>", inline=True)
    await ctx.author.send(embed=embed)


@client.command()
async def top(ctx, amount=10):
    profiles = cw_db.get_top_rank(int(amount if amount < 20 else 20))  # в дискорде ограничение по количеству полей
    embed = discord.Embed(colour=discord.Colour(0x7b03b9), )
    for profile in profiles:
        embed.add_field(name=f"{profile['ranks']['overall']['name']}", value=f"<@{profile['discord_id']}>")
    await ctx.send(embed=embed)


@commands.has_permissions(administrator=True)
@client.command()
async def remove(ctx, username):
    log.info(f'{ctx.author.name}: {ctx.message.content}')
    log.debug(f'{ctx.author.id}|{ctx.author.name} \n'
              f'{ctx.message}')
    profile = cw_db.get_profile_by_username(username)
    guild = client.get_guild(int(os.getenv("SERVER_ID")))
    roles = {
        't0': guild.get_role(os.getenv("TIER0")),
        't1': guild.get_role(os.getenv("TIER1")),
        't2': guild.get_role(os.getenv("TIER2"))
    }  # роли сервера
    tier_list = [roles["t0"], roles["t1"], roles["t2"]]
    member = guild.get_member(profile['discord_id'])  # профиль CW из MongoDB

    cw_db.remove_cw_profile(username)
    if member is not None:
        for role in tier_list:
            await member.remove_roles(role, reason=f'Removed {username} codewars profile by {ctx.author.name}')
    log.info(f'Профиль {username} удалён')
    await ctx.send(f'Профиль {username} удалён, мой Господин')


@client.command(aliases=['u'])
async def update(ctx):
    log.info(f'{ctx.author.name}: {ctx.message.content}')
    log.debug(f'{ctx.author.id}|{ctx.author.name} \n'
              f'{ctx.message}')
    profile = cw_db.get_profile_by_discord_id(ctx.author.id)
    if ctx.author.id == profile['discord_id']:
        cw_db.update_cw_profile(profile['username'], profile['discord_id'])
        return await ctx.send(f'Информация о профиле: `{profile["username"]}` успешно обновлена!')


@tasks.loop(seconds=int(os.environ.get('AUTO_UPDATE_DELAY')))
async def auto_update_cw_profiles():
    log.info('Updating profiles')
    await client.loop.run_in_executor(None, cw_db.update_all_profiles)


if __name__ == '__main__':
    client.run(TOKEN)
