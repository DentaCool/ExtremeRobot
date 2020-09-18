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
    if not cw.activation_check(username, code):
        log.debug(f'{ctx.command.name}'
                  f'\n{ctx.message}\n'
                  f'\tActivation Code: [{code}]\n'
                  f'\tActivation check: False')
        return await ctx.send('Указан не верный код активации либо указаный аккаунт не существует')
    if not cw_db.abuse_check(ctx.author.id):
        log.debug(f'{ctx.command.name}'
                  f'\n{ctx.message}\n'
                  f'\tActivation Code: [{code}]\n'
                  f'\tActivation check: True\n'
                  f'\tDuplicate check: False')
        return await ctx.send('Данный аккаунт уже привязан')
    # получаем роли сервера

    # extremecode discord server
    # Ммм, хардкод :clown:
    guild = client.get_guild(464822298537623562)
    tier0 = guild.get_role(671320134937215005)
    tier1 = guild.get_role(672103683118333953)
    tier2 = guild.get_role(672103803067301908)
    '''
    # test server
    guild = client.get_guild(743465592601837679)
    tier0 = guild.get_role(743466011763933244)
    tier1 = guild.get_role(743466116382457997)
    tier2 = guild.get_role(743466149332647976)
    '''
    # cw.get_rank возвращает число ранка. В кодварсе оно отрицательно ибо в будущем будут добавлены dan ранки
    rank = cw.get_rank(username)
    tier_list = {
        -8: [tier0],
        -7: [tier0],
        -6: [tier0, tier1],
        -5: [tier0, tier1],
        -4: [tier0, tier1, tier2],
        -3: [tier0, tier1, tier2],
        -2: [tier0, tier1, tier2],
        -1: [tier0, tier1, tier2]
        # когда будет tier3 !!!
    }
    # выдача ролей
    member = guild.get_member(ctx.author.id)
    for role in tier_list[int(rank)]:
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
async def top(ctx, amount=10):
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

    await ctx.send(embed=embed)


@commands.has_permissions(administrator=True)
@client.command()
async def remove(ctx, username):
    log.info(f'{ctx.author.name}: {ctx.message.content}')
    log.debug(f'{ctx.author.id}|{ctx.author.name} \n'
              f'{ctx.message}')
    profile = cw_db.get_profile_by_username(username)
    # роли тест сервера
    guild = client.get_guild(743465592601837679)
    tier0 = guild.get_role(743466011763933244)
    tier1 = guild.get_role(743466116382457997)
    tier2 = guild.get_role(743466149332647976)
    tier_list = [tier0, tier1, tier2]
    # профиль дискорда
    member = guild.get_member(profile['discord_id'])

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
