import configparser
import pymongo
import codewarse_api as sw

cfg = configparser.ConfigParser()
cfg.read('./config.ini')


mongo_client = pymongo.MongoClient(cfg['mongoDB']['url'],
                                   username=cfg['mongoDB']['username'],
                                   password=cfg['mongoDB']['password'])
db = mongo_client['Codewars']
users_col = db['users']


def insert_cw_profile(username, discord_id):
    profile = sw.get_user(username)
    profile['discord_id'] = discord_id
    if users_col.find_one(filter={'username': profile['username']}) is None\
            or users_col.find_one(filter={'discord_id': discord_id}) is None:
        users_col.insert_one(profile)


def update_cw_profile(username, discord_id):
    profile = sw.get_user(username)
    profile['discord_id'] = discord_id
    users_col.find_one_and_replace(filter={'username': profile['username']}, replacement=profile)


def remove_cw_profile(username):
    profile = sw.get_user(username)
    users_col.find_one_and_delete(filter={'username': profile['username']})


def abuse_check(discord_id):
    if users_col.find_one(filter={'discord_id': discord_id}) is None:
        return True
    return False
