#!/usr/bin/env python
from itertools import count
import requests
import os
import json
import pandas as pd
import csv
import datetime
import dateutil.parser
import unicodedata
import time
import tweepy
from collections import defaultdict

def auth():
    return "AAAAAAAAAAAAAAAAAAAAAIQYZAEAAAAAATW%2BKD0mMJh9ArxHgT2bBgCTkic%3DUpXveqtWdJwaELP3GHvKVfdOoJatuCAZKIbxovkteWssJhBgxC"

def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers

def connect_to_endpoint(url, headers, params, next_token = None):
    params['next_token'] = next_token   #params object received from create_url function
    response = requests.request("GET", url, headers = headers, params = params)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

def parse_handles(fname): #The file containing list of Wit profiles is passed as a parameter
    handles = []
    with open(fname) as file:
        i = 0
        for line in file: #For every line containing a handle in the file, the Twitter handle is added to a list
            if i == 0:
                i += 1
                continue
            handle = line.strip("\n").strip("\"").strip(" ")
            handle = handle.split(" ")[0]
            handles.append(handle)
    return handles[:5] #Returns the first 25 handles in the list

def does_follow_team(response, team_name="NYIslanders"):
    for entry in response['data']:
        if team_name == entry['username']:
            return True
    return False

    followers = []
    for username, fields in result.items():
        print(username)
        uid = fields['id']
   
        url = f"https://api.twitter.com/2/users/{uid}/following"
        query_params = {
            "user.fields": "id,username",
            "max_results": 1000
        }
        if 'pagination_token' in query_params:
            del query_params['pagination_token']
        response = connect_to_endpoint(url, headers, query_params)
        print(len(response1['data']))
        if does_follow_team(response):
            followers.append(username)
        else:
            metadata = response['meta']
            while 'next_token' in metadata:
                next_token = metadata['next_token']
                query_params1 = query_params
                query_params1['pagination_token'] = next_token
                response1 = requests.request("GET", url, headers=headers, params=query_params1)
                if response1.status_code != 200:
                    break
                response1 = response1.json()
                metadata = response1['meta']
                if does_follow_team(response1):
                    followers.append(username)
                print(len(response1['data']))

    print(followers)    


#def does_follow_team(handles, team_name):
#    for handle in handles:
#        url = f"https://api.twitter.com/2/users/by/username/following/{handle}"
#        query_params = {
#            "user.fields": "text"
#        }
#        result = connect_to_endpoint(url, headers, query_params)
#        #print(result)
        
def count_tweets(response, team_name="NYIslanders"): #Used to find both # of liked tweets and retweets
    cnt = 0
    if 'users' in response.includes:
        for entry in response.includes['users']:
            if team_name == entry.username: #Compares the ID of the original authors of the liked tweets to the NY Islanders Twitter ID
                cnt += 1 #If they are equal to each other add 1 to the count
    return cnt

#Inputs for the request
bearer_token = auth()
headers = create_headers(bearer_token)
handles = parse_handles("FanAPI/twitter_handles.csv")
result = defaultdict(dict)
invalid_users = []

#does_follow_team(handles, "NYIslanders")
client = tweepy.Client(bearer_token = "AAAAAAAAAAAAAAAAAAAAAIQYZAEAAAAAATW%2BKD0mMJh9ArxHgT2bBgCTkic%3DUpXveqtWdJwaELP3GHvKVfdOoJatuCAZKIbxovkteWssJhBgxC", wait_on_rate_limit=True)

usernames = ",".join(handles)
url = f"https://api.twitter.com/2/users/by"
query_params = {
    "usernames": usernames,
    "user.fields": "public_metrics"
}
response = connect_to_endpoint(url, headers, query_params)

for entry in response["data"]:
    result[entry['username']]['id'] = entry["id"] #Getting ID
    result[entry['username']]['followers_count'] = entry['public_metrics']["followers_count"]
    result[entry['username']]['following_count'] = entry['public_metrics']["following_count"]
#for entry in response['errors']:
#    invalid_users.append(entry['value']) #List of users with invalid Twitter accounts

with open('Metrics.csv', 'a', newline='',encoding='utf-8') as csvfile:
    header_key = ['UserName', 'Followers_Count','Following_Count','Likes_Count','Retweets_Count']
    new_val = csv.DictWriter(csvfile, fieldnames=header_key)
    new_val.writeheader()
    csvfile.close()
    
def get_likes():
    usernames = list(result.keys())
    for username in usernames:
        uid = result[username]['id']
        cnt = 0
        response = client.get_liked_tweets(uid, max_results=100, expansions="author_id") #Obtains all liked tweets from a user and returns the ID of the original authors
        cnt += count_tweets(response)

        metadata = response.meta
        while 'next_token' in metadata: #Pagination to retrieve more than 100 results
            next_token = metadata['next_token']
            response1 = client.get_liked_tweets(uid, max_results=100, expansions="author_id", pagination_token=metadata['next_token'])
            metadata = response1.meta
            cnt += count_tweets(response1)
            time.sleep(5)                
            break
        result[username]['likes_count'] = cnt
        #print(f"{username} likes count: {cnt}")     
    #time.sleep(855)
           

def get_retweets():
    usernames = list(result.keys())
    for username in usernames:
        uid = result[username]['id']
        cnt = 0
        response = client.get_users_tweets(uid, max_results=100, expansions=["referenced_tweets.id","referenced_tweets.id.author_id"]) 
        #Returns ID of the original tweet that was retweeted and the ID of the author of original tweet
        cnt += count_tweets(response)
        metadata = response.meta
        while 'next_token' in metadata: #Pagination to retrieve more than 100 results
            next_token = metadata['next_token']
            response1 = client.get_users_tweets(uid, max_results=100, expansions=["referenced_tweets.id", 
                                                "referenced_tweets.id.author_id"], pagination_token=metadata['next_token'])
            metadata = response1.meta
            cnt += count_tweets(response1)
            time.sleep(5)                
            break
        result[username]['retweets_count'] = cnt
        #print(f"{username} retweets count: {cnt}")

#Because of rate limiting, I am only getting the quote tweets for the last 100 tweets from NYIslanders
#For these last 100, none of the top 25 handles have quoted them so the count is 0.
def get_quote_tweets():
    nyislanders_id = "16651754"
    for tweet in tweepy.Cursor(client.get_users_tweets(nyislanders_id),max_results = 10).items(10):
        tweets = response
        quote_cnts = defaultdict(int)
        usernames = list(result.keys())
    
        for username in usernames:
            result[username]['quotes_count'] = 0
        for entry in tweets.data:
            tweet_id = entry.id
            response = client.get_quote_tweets(tweet_id, expansions=["referenced_tweets.id.author_id"])                                                                 
            if 'users' in response.includes:
                print(response.includes['users'])
                try:
                    for entry2 in response.includes['users']:
                        if entry2.username in usernames:
                            result[entry2.username]['quotes_count'] += 1
                            print(result[entry2.username]['quotes_count'])
                        print(len(response))       
                    time.sleep(10)
                except tweepy.TweepError as e:
                        print(e.reason)
                except StopIteration:
                        break



get_quote_tweets()
#get_likes()
#get_retweets()
#print(result)

# list followers
followers = []
print(f"Followers (accounts who follow {screen_name})")
for page in tweepy.Cursor(api.get_followers, screen_name=screen_name,
                          count=200).pages(10):
    for user in page:
        name = f"{user.id} - {user.name} (@{user.screen_name})"
        followers.append(name)
    print(len(page))
    
print(f"Followers: {len(followers)}")

# Store output from Python dictionary to CSV with header
#def append_to_csv(result, fileName):
#    with open('Metrics.csv', 'w', newline='') as csvfile:
#        header_key = ['UserName', 'Followers_Count','Following_Count','Likes_Count','Retweets_Count']
#        new_val = csv.DictWriter(csvfile, fieldnames=header_key)
#
#        new_val.writeheader()
#        csvfile.close()


#        for new_k in result:
#            new_val.writerow({'UserName': new_k, 'Followers_Count': result[new_k]['followers_count'], 
#                            'Following_Count': result[new_k]['following_count'], 
#                           'Likes_Count':result[new_k]['likes_count'], 
#                           'Retweets_Count':result[new_k]['retweets_count']})
#        csvfile.close()

#def append_to_csv(result, fileName):

    #A counter variable
#    counter = 0

    #Open OR create the target CSV file
#    csvFile = open('Metrics.csv', "a", newline="", encoding='utf-8')
#    csvWriter = csv.writer(csvFile)

    #Loop through each tweet
#    for new_k in result:
#        new_val.writerow({'UserName': new_k, 'Followers_Count': result[new_k]['followers_count'], 
 #                           'Following_Count': result[new_k]['following_count'], 
  #                          'Likes_Count':result[new_k]['likes_count'], 
   #                         })
    #    counter += 1

    # When done, close the CSV file
    #csvFile.close()

    # Print the number of tweets for this iteration
   # print("# of Tweets added from this response: ", counter) 

#append_to_csv(result, "Metrics.csv")


#def create_url(start_date, end_date, max_results = 10):
    
#    search_url = "https://api.twitter.com/2/users/by" #Change to the endpoint you want to collect data from

#   #change params based on the endpoint you are using
#    query_params = {
#                    'usernames': usernames,
#                    'user.fields': 'public_metrics',
#                   }
#    return (search_url, query_params)


 

#keyword = "xbox lang:en"
#start_time = "2021-03-01T00:00:00.000Z"
#end_time = "2021-03-31T00:00:00.000Z"
#max_results = 100

# does_follow_team(handles, "NYIslanders")
#client = tweepy.Client(bearer_token = "AAAAAAAAAAAAAAAAAAAAAIQYZAEAAAAAATW%2BKD0mMJh9ArxHgT2bBgCTkic%3DUpXveqtWdJwaELP3GHvKVfdOoJatuCAZKIbxovkteWssJhBgxC",wait_on_rate_limit=True)

#usernames = ",".join(handles)
#url = f"https://api.twitter.com/2/users/by"
#query_params = {
#    "usernames": usernames,
#    "user.fields": "public_metrics"
#}

#url = create_url(start_time,end_time, max_results)
#response = connect_to_endpoint(url[0], headers, url[1])
#print(json.dumps(response, indent=4, sort_keys=True))

#for entry in response["data"]:
#    result[entry['username']]['id'] = entry["id"] #Getting ID
#    result[entry['username']]['followers_count'] = entry['public_metrics']["followers_count"]
#   result[entry['username']]['following_count'] = entry['public_metrics']["following_count"]




#with open('Metrics.csv', 'a', newline='',encoding='utf-8') as csvfile:
#   header_key = ['UserName', 'Followers_Count','Following_Count','Likes_Count','Retweets_Count']
#   new_val = csv.DictWriter(csvfile, fieldnames=header_key)
#   new_val.writeheader()
 #   csvfile.close()


