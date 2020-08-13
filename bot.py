import hashlib
import codewarse_api as cw
import cw_mongo as cw_db
from discord.ext import commands
from discord import Permissions

TOKEN = 'NTU4MDAwMTYwMTg2MzAyNDc0.XJKMJQ.jaEvp7vR_-kTY4dG9m97zBwdpjk'
client = commands.Bot(command_prefix='ex/')


@client.command()
async def check(ctx, username):
    # получаем код для валидации аккаунта в виде md5 из никнейма
    code = hashlib.md5(ctx.author.name.encode()).hexdigest()
    print(code)
    print(cw.activation_check(username, code))

    if cw.activation_check(username, code):
        # получаем роли сервера
        ''' 
        # extreemecode discord server
        guild = client.get_guild(464822298537623562)
        tier0 = guild.get_role(671320134937215005)
        tier1 = guild.get_role(672103683118333953)
        tier2 = guild.get_role(672103803067301908)
        '''
        guild = client.get_guild(743465592601837679)
        tier0 = guild.get_role(743466011763933244)
        tier1 = guild.get_role(743466116382457997)
        tier2 = guild.get_role(743466149332647976)

        # cw.get_rank возвращает число ранка. В кодварсе оно отрицательно ибо в будущем будут добавлены dan ранки
        rank = cw.get_rank(username)
        tier_list = {
            -8: [tier0],
            -7: [tier0],
            -6: [tier0, tier1],
            -5: [tier0, tier1],
            -4: [tier0, tier1, tier2],
            -3: [tier0, tier1, tier2]
            # когда будет tier3 !!!
        }

        member = guild.get_member(ctx.author.id)
        for role in tier_list[int(rank)]:
            await member.add_roles(role, reason=f'{ctx.author.name} with Rank: {rank}')
        cw_db.insert_cw_profile(username)
        # await ctx.send('Поздровляю, вы теперь не лох!')
        await ctx.send('Проверка успешно пройдена!')


@client.command()
async def codewars(ctx):
    await ctx.author.send(content = f'''
  Привет! Сейчас мы интегрируем твой профиль CodeWars
  1. Зайди в настройки профиля: https://www.codewars.com/users/edit
  2. Введи в поле Clan следующий код активации: `{hashlib.md5(ctx.author.name.encode()).hexdigest()}`
  3. Скопируй свой Username
  4. Сохрани профиль
  5. Отправь сюда свой Username в следующем формате ex/check Username
  6. PROFIT
  7. ???
''', )


@commands.has_permissions(administrator=True)
@client.command()
async def remove(ctx,username):
    cw_db.remove_cw_profile(username)
    await ctx.send(f'Профиль {username} удалён')

client.run(TOKEN)
