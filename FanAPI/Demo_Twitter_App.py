import tweepy
import config
import csv

client = tweepy.Client(bearer_token = config.BEARER_TOKEN)

#Search for query and no retweets
query = "Bracket -is:retweet"
#query = 'from:BuffaloSabres -is:retweet'

#Use expansions for getting user data for each tweet
response = client.search_recent_tweets(query = query, max_results =100, tweet_fields=['created_at'], expansions = ['author_id'] )

#Create a dictionary for users information so we can print user info
users = {u['id']: u for u in response.includes['users']}

filename = 'Bracket_tweets.csv'

#with open(file_name, 'a+') as filehandler:
with open (filename, 'w', encoding='utf-8') as csvFile:
    csvWriter = csv.writer(csvFile) 
    csvWriter.writerow(["ID","UserName","Created_at","Text"])
    for tweet in response.data:
        if users[tweet.author_id]:
            user = users[tweet.author_id]
            csvWriter.writerows([[tweet.id,user.username,tweet.created_at,tweet.text]])



