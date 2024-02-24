from collections import Counter
import tweepy
import config
import csv
import time
import json
client = tweepy.Client(bearer_token = config.BEARER_TOKEN)

# the screen name of the user
screen_name = "NYIslanders"

# fetching the user
auth = client.get_user(username=screen_name)

ID = auth.data.id

# api = tweepy.API(auth)
    
def get_followers(screen_name):
    print('Getting Follower list of ',screen_name)
    followers = []
    followers_screenNames = []
    users = tweepy.Cursor(client.get_users_followers, screen_name='@'+screen_name, wait_on_rate_limit=True,count=100)    
    for user in users.items():
        try:
            followers.append(user)
            followers_screenNames.append(user.screen_name)
        except tweepy.TweepError as e:
            print("Going to sleep:", e)
            time.sleep(60)
    
    print('Fetched number of followers for '+screen_name+' : ',len(followers))
    return followers,followers_screenNames

def get_following(screen_name):
    print('Getting Following list of ',screen_name)
    friends = []
    friends_screenName = []
    users = tweepy.Cursor(api.friends, screen_name='@'+screen_name,
            wait_on_rate_limit=True,count=200)
    for user in users.items():
        try:
            friends.append(user)
            friends_screenName.append(user.screen_name)
        except tweepy.TweepError as e:
            print("Going to sleep:", e)
            time.sleep(60)
    print('Fetched number of following for '+screen_name+' : ',len(friends))            
    return friends,friends_screenName

def fetch_data():
    people = list(get_followers('NYIslanders'))[0]
    people.extend(list(get_following('NYIslanders')[0]))
    data = {}
    for user in people:
        try:
            print('Fetching data of ',user.name)
            ob = {
                'ID':user.id,
                'Name':user.name,
                'StatusesCount':user.statuses_count,
                'Follower_Count':user.followers_count,
                'Following_Count':user.friends_count,
                'Followers':list(get_followers(user.screen_name))[1],
                'Following':list(get_following(user.screen_name))[1],
                }
            print(ob)
            data[user.screen_name].append(ob)
            print('Data saved, moving on to next user\n\n')
        except Exception as ex:
            print(ex)
            pass
    
    with open('data.txt', 'w') as outfile:
        json.dump(data, outfile)


fetch_data()            
