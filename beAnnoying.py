'''
Created on Mar 27, 2017

@author: andrew
'''
import copy
import os
import signal
import subprocess
import sys
import time

import credentials
from utils.dataIO import DataIO


class Overseer():
    def __init__(self):
        self.db = DataIO(TESTING, credentials.test_database_url)
        self.shards = {}

TESTING = False
RUNNING = True
if "test" in sys.argv:
    TESTING = True
bot = Overseer()

def init():
    signal.signal(signal.SIGTERM, sigterm_handler)
    launch_shards()
    clean_shard_servers()

def loop():
    time.sleep(30)
    if RUNNING:
        check_shards()
    
    
def launch_shards():
    for shard in range(int(os.environ.get('SHARDS', 1))):
        if TESTING:
            print("Launching shard test {}".format(shard))
            bot.shards[shard] = subprocess.Popen(['python3', 'dbot.py', '-s', str(shard), 'test'])
        else:
            print("Launching shard production {}".format(shard))
            bot.shards[shard] = subprocess.Popen(['python3', 'dbot.py', '-s', str(shard)])
        time.sleep(10)
    print("Shards launched: {}".format({shard: process.pid for shard, process in bot.shards.items()}))
    
def check_shards():
    for shard, process in bot.shards.items():
        if process.poll() is not None:
            print('Shard {} crashed with exit code {}, restarting...'.format(shard, process.returncode))
            if TESTING:
                print("Launching shard test {}".format(shard))
                bot.shards[shard] = subprocess.Popen(['python3', 'dbot.py', '-s', str(shard), 'test'])
            else:
                print("Launching shard production {}".format(shard))
                bot.shards[shard] = subprocess.Popen(['python3', 'dbot.py', '-s', str(shard)])
            
    
def clean_shard_servers():
    shard_servers = bot.db.jget('shard_servers', {0: 0})
    num_shards = int(os.environ.get('SHARDS', 1))
    temp = copy.copy(shard_servers)
    for shard in shard_servers.keys():
        if int(shard) >= num_shards:
            del temp[shard]
            print("Overseer process deleted server data for shard {}".format(shard))
    bot.db.jset("shard_servers", temp)

def sigterm_handler(_signum, _frame):
    global RUNNING
    RUNNING = False
    print("Overseer caught SIGTERM, sleeping for 15!")
    time.sleep(15)
    sys.exit(0)
    
if __name__ == '__main__':
    init()
    while True:
        loop()