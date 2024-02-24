from collections import Counter
import tweepy
import config
import csv

client = tweepy.Client(bearer_token = config.BEARER_TOKEN)

# the screen name of the user
screen_name = "NYIslanders"


# fetching the user
user1 = client.get_user(username=screen_name)

# fetching the ID
ID = user1.data.id

# print(f"The Twitter ID is {user.data.id}.")

users = client.get_users_followers(id=ID, max_results = 1000)
count = 0
for user in users.data:
    # print(user.username)
    count = count +1
print(count)

users1 = client.get_users_following(id=ID, max_results = 1000)

count = 0
for user in users1.data:
    # print(user.username)
    count = count +1
print(count)


for response in tweepy.Paginator(client.get_users_followers, 16651754,
                                    max_results=1000, limit=5):
    print(response.meta)



    print('Getting Follower list of ',screen_name)
    followers = []
    followers_screenNames = []
    users = tweepy.Paginator(client.get_users_followers, 16651754, screen_name='@'+screen_name,
                                    max_results=1000, limit=5):
                print(users.meta)

    users = tweepy.Cursor(client.get_users_followers, screen_name='@'+screen_name, wait_on_rate_limit=True,count=200)    
    for user in users.items():
        try:
            followers.append(user)
            followers_screenNames.append(user.screen_name)
        except tweepy.TweepError as e:
            print("Going to sleep:", e)
            time.sleep(60)
    
    print('Fetched number of followers for '+screen_name+' : ',len(followers))
    return followers,followers_screenNames






