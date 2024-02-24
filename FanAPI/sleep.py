import os
import sys
import json
import time
import math
from tweepy import Cursor
import tweepy
from tweepy import OAuthHandler
import datetime
import config
    
    #auth = OAuthHandler(consumer_key, consumer_secret)
    #auth.set_access_token(access_token, access_token_secret)
client = tweepy.Client(bearer_token = config.BEARER_TOKEN, wait_on_rate_limit=True)
   # api = tweepy.API(auth, wait_on_rate_limit=True)
MAX_FRIENDS = 10000
    
def paginate(items, n):
    """Generate n-sized chunks from items"""
    for i in range(0, len(items), n):
        yield items[i:i+n]
        
def get_followers(screen_name):
    # get followers for a given user
    #fname = "users/{}/followers.json".format(screen_name)
    fname = f"https://api.twitter.com/2/users/by/username/{handle}"
    max_pages = math.ceil(MAX_FRIENDS / 5000)
    with open(fname, 'w') as f:
        for followers in Cursor(client.followers_ids, screen_name=screen_name).pages(max_pages):
            for chunk in paginate(followers, 100):
                users = client.lookup_users(user_ids=chunk)
                for user in users:    
                    f.write(json.dumps([user.id, user.screen_name, user.location, str(user.created_at)], sort_keys=True)+"\n")                 
                if len(followers) == 5000:
                    print("More results available. Sleeping for 60 seconds to avoid rate limit")
                    time.sleep(60)
        print("task completed for " + screen_name)
get_followers('NYIslanders')
