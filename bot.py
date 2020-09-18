import os
import hashlib
from codewarse_api import api as cw
import cw_mongo as cw_db
import discord
from discord.ext import commands, tasks
import logging

TOKEN = os.environ.get('TOKEN')
command_prefix = 'ex/'
client = commands.Bot(command_prefix=command_prefix)

logging.basicConfig(filename='BOT-ERRORS.log', filemode='a')


@client.event
async def on_ready():
    auto_update_cw_profiles.start()
    await client.change_presence(status=discord.Status.idle, activity=discord.Game(name=f'{command_prefix}codewars'))


@client.command()
@commands.cooldown(rate=3, per=5, type=commands.BucketType)
async def check(ctx, username):
    """
    Провверить свой профиль codewars'а.
    :param ctx:
    :param username: имя пользователя
    :return:
    """
    # получаем код для валидации аккаунта в виде md5 из discord id
    code = hashlib.md5(str(ctx.author.id).encode()).hexdigest()
    # пытаемся проверить аккаунт
    if not cw.activation_check(username, code):
        # если код не правидьный:
        await ctx.send(embed=discord.Embed(title=':x: Указан не верный код активации либо указаный аккаунт не '
                                                 'существует!', color=0xf00))

    elif not cw_db.abuse_check(ctx.author.id):
        # если аккаунт уже был когда-то привязан:
        await ctx.send(embed=discord.Embed(title=':x: Аккаунт уже был привязан!', color=0xf00))

    else:
        try:
            # Роли оснавного сервера (ExtremeCode)
            server = client.get_guild(464822298537623562)
            roles = {
                'server': client.get_guild(464822298537623562),
                't0': server.get_role(671320134937215005),
                't1': server.get_role(672103683118333953),
                't2': server.get_role(672103803067301908)
            }
            '''
            # Ролли тестого сервера
            roles = {
                'server': client.get_guild(743465592601837679),
                't0': server.get_role(743466011763933244),
                't1': server.get_role(743466116382457997),
                't2': server.get_role(743466149332647976)
            }
            '''
            # cw.get_rank возвращает число ранка. В кодварсе оно отрицательно ибо в будущем будут добавлены dan ранки
            rank = cw.get_rank(username)
            tier_list = {
                -8: [roles['t0']],
                -7: [roles['t0']],
                -6: [roles['t0'], roles['t1']],
                -5: [roles['t0'], roles['t1']],
                -4: [roles['t0'], roles['t1'], roles['t2']],
                -3: [roles['t0'], roles['t1'], roles['t2']],
                -2: [roles['t0'], roles['t1'], roles['t2']],
                -1: [roles['t0'], roles['t1'], roles['t2']],
            }
            # выдача ролей
            member = server.get_member(ctx.author.id)

            for role in tier_list[int(rank)]:
                await member.add_roles(role, reason=f'{ctx.author.name} with Rank: {rank}')

            cw_db.insert_cw_profile(username, ctx.author.id)
            await ctx.send(embed=discord.Embed(title='Вы успешно прошли проверку!', color=0x15ff00))
        except Exception as e:
            logging.error(e)
            await ctx.send(embed=discord.Embed(title=':x: Ой, при проверке профиля произошла ошибка!', color=0xf00))


@client.command()
async def codewars(ctx):
    """
    Краткая инструкция для пользователей бота.
    Отправляет сообщения с пошаговой привязкой профиля кодварса
    """
    await ctx.author.send(content=f'''
  Привет {ctx.author.name}, следуй это инструкции чтобы привязать профиль!
  **1.** Зайди в настройки профиля: https://www.codewars.com/users/edit
  **2.** Введи в поле Clan следующий код активации: `{hashlib.md5(str(ctx.author.id).encode()).hexdigest()}`
  **3.** Скопируй свой Username
  **4.** Сохрани профиль
  **5.** Отправь сюда свой Username в следующем формате ex/check Username
''', )


@client.command()
@commands.cooldown(rate=1, per=5, type=commands.BucketType)
async def top(ctx, amount: int = 10):
    """
    Получить топ самых лучших профилей
    :param ctx:
    :param amount: Кооличество участников в будущем сообщении
    """
    profiles = cw_db.get_top_rank(amount)
    embed = discord.Embed(colour=discord.Colour(0x7b03b9), )

    embed.set_author(name=f"Top {amount}")

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
    """
    Удалить профиль пользователя
    P.S Доступно только администраторам сервера!
    :param ctx:
    :param username: имя пользователя
    """
    try:
        cw_db.remove_cw_profile(username)
        await ctx.send(embed=discord.Embed(title=f'Профиль {username} был успешно удалён!', color=0x15ff00))

    except Exception as e:
        logging.error(e)
        await ctx.send(embed=discord.Embed(title=':x: Упс, я не смог удалить профиль!', color=0xf00))


@client.command()
@commands.cooldown(rate=1, per=5, type=commands.BucketType)
async def update(ctx, username):
    """
    Обновляет профиль пользователя
    :param ctx:
    :param username: имя пользователя
    """
    try:
        profile = cw_db.get_profile(username)
        if ctx.author.id == profile['discord_id']:
            cw_db.update_cw_profile(username, profile['discord_id'])
            await ctx.send(embed=discord.Embed(title='Информация о профиле была успешно обновлена!',
                                               color=0x15ff00))
    except Exception as e:
        logging.error(e)
        await ctx.send(embed=discord.Embed(title=':x: Произошла **ошибка**, пожалуста сообщите разработчику!',
                                           color=0xf00))


@tasks.loop(seconds=30)
async def auto_update_cw_profiles():
    """
    Автоматическая проверка профилей каждые 30 секунд!
    (Это число может изменится в будущем!)
    :return:
    """
    try:
        cw_db.update_all_profiles()
        logging.log(level=1, msg='Проверка профилей пройденна успешно!')
    except Exception as e:
        logging.error(f'Ошибка при обговленни сообщений: {e}')


if __name__ == '__main__':
    client.run(TOKEN)
