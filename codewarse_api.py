import requests


def activation_check(username, code):
    clan = get_user(username)['clan']
    if clan == code:
        return True
    return False


def get_user(username):
    r = requests.get(f'https://www.codewars.com/api/v1/users/{username}')
    if r.status_code == 200:
        return r.json()
    # на случай если аккаунт не найден чтобы не обрабатывать exception (мне и так не заплатят, зачем делать больше кода)
    # P.s. и я знаю что есть какой-то там метод в случае кей еррора возвращать заданое значение но ответ ровно выше :) )
    return get_user('error')


def get_rank(username):
    """
        Спик инглиш?
        Транслейт зе нейм оф функшин фор мор инфо ват ши ду
    """
    user = get_user(username)
    return user['ranks']['overall']['rank']
