import requests


class CodewarsAPI:

    def activation_check(self, username, code):
        clan = self.get_clan(username)
        if clan == code:
            return True
        return False

    def get_user(self, username):
        r = requests.get(f'https://www.codewars.com/api/v1/users/{username}')
        if r.status_code == 200:
            return r.json()
        return self.get_user('error')

    def get_clan(self, username):
        user = self.get_user(username)
        return user['clan']

    def get_rank(self, username):
        user = self.get_user(username)
        return user['ranks']['overall']['rank']


api = CodewarsAPI()
