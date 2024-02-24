import tweepy
import config
import csv

client = tweepy.Client(bearer_token = config.BEARER_TOKEN)

# the screen name of the user
screen_name = "NYIslanders"


# fetching the user

#user = client.get_user(username=screen_name)

# using user_fields
user = client.get_user(username = screen_name, user_fields=['public_metrics'])
user_metrics = user.data['public_metrics']
followers = user_metrics['followers_count']
following = user_metrics['following_count']
tweet_count = user_metrics['tweet_count']
retweet_count = user_metrics['listed_count']

#user.data.public_metrics.quote_count

print(followers,following,tweet_count,retweet_count)
filename = 'Metrics.csv'

#with open(file_name, 'a+') as filehandler:
with open (filename, 'w', encoding='utf-8') as csvFile:
    csvWriter = csv.writer(csvFile) 
    csvWriter.writerow(["Followers_Count","Following_Count","Tweet_Count","Retweet_Count"])
    csvWriter.writerows([[followers,following,tweet_count,retweet_count]])


