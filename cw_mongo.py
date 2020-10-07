import os
import pymongo
from codewarse_api import api as sw

mongo_url = f"mongodb://{os.environ['MONGODB_USERNAME']}:{os.environ['MONGODB_PASSWORD']}@{os.environ['MONGODB_HOSTNAME']}:27017/{os.environ['MONGODB_DATABASE']}?authSource=admin"
mongo_client = pymongo.MongoClient(mongo_url)
db = mongo_client['Codewars']
users_col = db['users']


def abuse_check(discord_id: int):
    if users_col.find_one(filter={'discord_id': discord_id}) is None:
        return True
    return False


def insert_cw_profile(username: str, discord_id: int):
    profile = sw.get_user(username)
    profile['discord_id'] = discord_id
    if users_col.find_one(filter={'username': profile['username']}) is None \
            or users_col.find_one(filter={'discord_id': discord_id}) is None:
        users_col.insert_one(profile)


def get_all_cw_profiles():
    profiles = list(users_col.find({}))
    return profiles


def get_top_rank(amount: int):
    profiles = get_all_cw_profiles()
    ls = sorted(profiles, key=lambda item: item['ranks']['overall']['score'])
    return ls[amount::-1]


def get_profile_by_username(username):
    return users_col.find_one({'username': username})


def get_profile_by_discord_id(discord_id):
    return users_col.find_one({'discord_id': discord_id})


def update_cw_profile(username: str, discord_id: int):
    profile = sw.get_user(username)
    profile['discord_id'] = discord_id
    users_col.find_one_and_replace(filter={'username': profile['username']}, replacement=profile)


def update_all_profiles():
    profiles = get_all_cw_profiles()
    for profile in profiles:
        update_cw_profile(profile['username'], profile['discord_id'])
        # print(f'Profile {profile["username"]} updated!')


def remove_cw_profile(username: str):
    profile = sw.get_user(username)
    users_col.find_one_and_delete(filter={'username': profile['username']})

# p.s. Почему codewarse_api.py сделано классом, а этот файл нет?
# ¯\_(ツ)_/¯
