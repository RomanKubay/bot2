from pymongo import MongoClient
from datetime import datetime
# from random import randint
import config

# load database
print("Підключаємось до MongoDB...")
client = MongoClient(config.MONGODB_HOST)
tasksdb = client.ukrwordsbot2.tasks
usersdb = client.ukrwordsbot2.users
wordsdb = client.ukrwordsbot2.words

print("Скачуємо всі необхідні дані...")
# words = {}; for i in range(3, 9): words[i] = wordsdb.find_one({"_id": i}) # Всі слова
sort_tasks = [ task for task in tasksdb.find({'type': 'sort'}) ]
heard_tasks = [ task for task in tasksdb.find({'type': 'heard'}) ]
known_tasks = [ task['word'] for task in tasksdb.find({'type': 'known'}) ]
whitelist = [ user['_id'] for user in usersdb.find({"_id": { "$gt": 0 }}) ]
blacklist = [ user for user in usersdb.find_one({'_id': 0})['blacklist'] ]

# buzy_tasks = {'sort': [], 'heard': [], 'known': []}
sorti, heardi = -1, -1
users_temp_data = {}
last_actions = []

def get_task_sort(user_id:int):
    # remove_prev_word = get_state(user_id) in buzy_tasks['sort']
    # tasks = [task for task in tasksdb.find({'type': 'sort'}) if not task['word'] in buzy_tasks['sort']]
    # if remove_prev_word: buzy_tasks['sort'].remove(get_state(user_id))
    # if len(tasks) == 0: return None
    
    # task = tasks[sorti]
    # set_state(user_id, task['word'])
    # return task, len(tasks)
    global sorti, sort_tasks
    if sorti >= len(sort_tasks):
        sort_tasks = [ task for task in tasksdb.find({'type': 'sort'}) ]
        sorti = -1
        if len(sort_tasks) == 0: return None
    sorti += 1
    return sort_tasks[sorti]
def sort_word(word:str, level:int, user_id:int):
    l = len(word)
    if tasksdb.find_one({'type': 'sort', 'word': word}) is None: return
    tasksdb.delete_one({'type': 'sort', 'word': word})
    wordsdb.update_one({'_id': l}, {'$push': {str(level): word}})
    usersdb.update_one({'_id': user_id}, {'$inc': {'tasks': 1}})

def get_task_heard(user_id:int):
    # remove_prev_word = get_state(user_id) in buzy_tasks['heard']
    # tasks = [task for task in tasksdb.find({'type': 'heard'}) if not task['word'] in buzy_tasks['heard']]
    # if remove_prev_word: buzy_tasks['heard'].remove(get_state(user_id))
    # if len(tasks) == 0: return None
    
    # task = tasks[randint(0, len(tasks))]
    # set_state(user_id, task['word'])
    # return task, len(tasks)
    global heardi, heard_tasks
    if heardi >= len(heard_tasks):
        heard_tasks = [ task for task in tasksdb.find({'type': 'heard'}) ]
        heardi = -1
        if len(heard_tasks) == 0: return None
    heardi += 1
    return heard_tasks[heardi]

def heard_word(word:str, level:int, user_id:int):
    l = len(word)
    if tasksdb.find_one({'type': 'heard', 'word': word}) is None: return
    tasksdb.delete_one({'type': 'heard', 'word': word})
    wordsdb.update_one({'_id': l}, {'$push': {str(level): word}})
    usersdb.update_one({'_id': user_id}, {'$inc': {'tasks': 1}})
def get_rate_word(word:str, task_type:str) -> int:
    return tasksdb.find_one({'type': task_type, 'word': word})['rate']

def get_task_known(user_id:int):
    pass
    # tasks = [task for task in known_tasks if not task['word'] in buzy_tasks['known']]
    # if len(tasks) == 0: return None
    
    # task = tasks[randint(0, len(tasks))]
    # set_state(user_id, task['word'])
    # return task


def new_task(type:str, word:str, rate:int):
    tasksdb.insert_one({'type': type, 'word': word, 'rate': rate, 'wordleng': len(word)})
def delete_task(filter): tasksdb.delete_one(filter)


def new_user(id:int, name:str, username:str):
    if not usersdb.find_one({'_id': id}) is None: return
    usersdb.insert_one({'_id': id, 'name': name, 'username': username, 'tasks': 0})
    whitelist.append(id)
def get_user(user_id:int): return usersdb.find_one({'_id': user_id})
def get_all_users(): return usersdb.find({"_id": { "$gt": 1 }})
def update_user(user): return usersdb.update_one({'_id': user.id}, {'$set': {'name': user.full_name, 'username': user.username}})
def ban_user(user_id:int):
    if user_id in blacklist: return
    blacklist.append(user_id)
    usersdb.update_one({'_id': 0}, {'$push': {'blacklist': user_id}})
def unban_user(user_id:int):
    if not user_id in blacklist: return
    blacklist.remove(user_id)
    usersdb.update_one({'_id': 0}, {'$pull': {'blacklist': user_id}})

def get_user_temp(user_id:int) -> dict:
    if not user_id in users_temp_data:
        users_temp_data[user_id] = {'state': None, 'msg': None}
    return users_temp_data[user_id]
def get_state(user_id:int) -> str | None: return get_user_temp(user_id)['state']
def set_state(user_id:int, state:str): users_temp_data[user_id]['state'] = state
def get_lm(user_id:int) -> int | None: return get_user_temp(user_id)['msg'] # Get last bot message
def set_lm(user_id:int, msg:int): users_temp_data[user_id]['msg'] = msg

def get_stats():
    stats = {}
    words_count = 0
    for t in ['sort', 'heard', 'known']:
        stats[t] = tasksdb.count_documents({'type': t})
        words_count += stats[t]
    stats['words'] = words_count

    words = wordsdb.find({"_id": { "$gt": 0 }})#; print(len(list(words)))
    easy_split, normal_split, hard_split = [0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]
    stats['easy']=0; stats['normal']=0; stats['hard']=0; stats['saved']=0
    for i in range(6):
        easy_split[i] = len(words[i]['0'])
        normal_split[i] = len(words[i]['1'])
        hard_split[i] = len(words[i]['2'])
        stats['easy'] += easy_split[i]
        stats['normal'] += normal_split[i]
        stats['hard'] += hard_split[i]
        stats['saved'] += easy_split[i]+normal_split[i]+hard_split[i]
    stats['easy_split'] = [easy_split[i] for i in range(6)]
    stats['normal_split'] = [normal_split[i] for i in range(6)]
    stats['hard_split'] = [hard_split[i] for i in range(6)]
    stats['saved_split'] = [easy_split[i]+normal_split[i]+hard_split[i] for i in range(6)]

    users = []
    complete_count = 0
    lst = [(u['name'], u['tasks']) for u in usersdb.find({"_id": { "$gt": 1 }})]
    lst.sort(key=secondElement, reverse=True)
    for u in lst:
        users.append(u)
        complete_count += u[1]
    stats['users'] = users
    stats['complete'] = complete_count

    return stats

def add_action(action:str):
    global last_actions
    today = datetime.today()
    hour = today.hour + 2
    if hour >= 24: hour =- today.hour
    action = f'\n({hour}:{today.minute}:{today.second}) {action};'
    last_actions.insert(0, action)
    if len(last_actions) > config.max_history_leng_full: last_actions.pop()

def get_last_actions(full:bool=False) -> str:
    global last_actions
    text = f'🛃 Останні дії користувачів ({len(last_actions)} записів)\n'

    if (full):
        for a in last_actions: text += a
    else:
        i = 0
        for a in last_actions:
            text += a
            i += 1
            if i > config.max_history_leng: break
    return text

def secondElement(_): return _[1]

# Цей код щось додасть до всіх користувачів
#users.update_many({"_id": { "$gt": 1 }}, {"$set": { f"settings.send": 1 }})
