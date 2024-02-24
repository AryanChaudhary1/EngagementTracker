import tweepy
import config

client = tweepy.Client(bearer_token = config.BEARER_TOKEN)

#Search for query and no retweets
query = "RJ's Best Calls Bracket  -is:retweet"

#Use expansions for getting user data for each tweet
response = client.search_recent_tweets(query = query, max_results =100, tweet_fields=['created_at'], expansions = ['author_id'] )

#Create a dictionary for users information so we can print user info
users = {u['id']: u for u in response.includes['users']}

for tweet in response.data:
    if users[tweet.author_id]:
       user = users[tweet.author_id]
    print(tweet.id)
    print(user.username)
    print(tweet.created_at)
    print(tweet.text)