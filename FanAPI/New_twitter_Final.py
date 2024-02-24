#!/usr/bin/env python
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
#import logging
 
#logging.basicConfig(level=logging.DEBUG)

def auth():
    return "Your token here"

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
    return handles[:5] #Returns the first 5 handles in the list

        
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

client = tweepy.Client(bearer_token = "Your token here", wait_on_rate_limit=True)


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
#   invalid_users.append(entry['value']) #List of users with invalid Twitter accounts

    
def does_follow_team(response, team_name="NYIslanders"):
    for entry in response['data']:
        if team_name == entry['username']:
            return True
    return False

followers = []
for username, fields in result.items():
    uid = fields['id']
   
    url = f"https://api.twitter.com/2/users/{uid}/following"
    query_params = {
        "user.fields": "id,username",
        "max_results": 1000
    }
    if 'pagination_token' in query_params:
        del query_params['pagination_token']
    response = connect_to_endpoint(url, headers, query_params)
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

print(followers)
    
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
            break
        result[username]['likes_count'] = cnt
        #print(f"{username} likes count: {cnt}")
           

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
            break
        result[username]['retweets_count'] = cnt
        #print(f"{username} retweets count: {cnt}")

#Because of rate limiting, Getting the last 100 tweets from NYIslanders
#For these last 100 tweets, if none of the top 5 handles have quoted, the count is 0.
def get_quote_tweets():
    nyislanders_id = "16651754"
    tweets = client.get_users_tweets(nyislanders_id, max_results=100) #Getting last 100 tweets from NY Islanders
    quote_cnts = defaultdict(int)
    usernames = list(result.keys())
    for username in usernames:
        result[username]['quotes_count'] = 0
    for entry in tweets.data[:25]: #Takes last 25 tweets from the 100 NY Islanders tweets
        tweet_id = entry.id #Gets Tweet ID of 25 NY Islanders tweets
        #Obtains all quote tweets of a particular tweet
        response = client.get_quote_tweets(tweet_id, expansions=["referenced_tweets.id.author_id"]) 
        if 'users' in response.includes:
            for entry2 in response.includes['users']:
                if entry2.username in usernames: #If any author of a quote tweet is in the list of usernames
                    result[entry2.username]['quotes_count'] += 1 #If this condition is true, then add 1 to the quote tweet count
                      

def compute_engagement_score():
    eng_score = []
    for user in result.keys():
        eng_count = result[user]['likes_count']+result[user]['retweets_count']+result[user]['quotes_count']
        eng_score.append([user, eng_count])
   
    min_val = min([x[1] for x in eng_score]) #Minimum engagement score out of 5 users
    max_val = max([x[1] for x in eng_score]) #Maximum engagement score out of 5 users

    for i in range(len(eng_score)):
        result[eng_score[i][0]]['eng_score'] = eng_score[i][1]
        result[eng_score[i][0]]['eng_score_rank'] = 10 * (eng_score[i][1]-min_val)/(max_val-min_val)
        #Standard formula for min/max scaling: Gives a number from 0 to 1 which when multiplied by 10 gives engagement score                    

get_likes()
get_retweets()
get_quote_tweets()
compute_engagement_score()
print(result)

# Store output from Python dictionary to CSV with header
with open('Metrics.csv', 'w', newline='') as csvfile:
    header_key = ['UserName', 'Followers_Count','Following_Count','Likes_Count','Retweets_Count', 'Engagement_Score', 
                                                                                                'Engagement_Score_Rank']
    new_val = csv.DictWriter(csvfile, fieldnames=header_key)

    new_val.writeheader()

    for new_k in result:
        new_val.writerow({'UserName': new_k, 'Followers_Count': result[new_k]['followers_count'], 
                            'Following_Count': result[new_k]['following_count'], 
                            'Likes_Count': result[new_k]['likes_count'], 
                            'Retweets_Count': result[new_k]['retweets_count'],
                            'Engagement_Score': result[new_k]['eng_score'],
                            'Engagement_Score_Rank': result[new_k]['eng_score_rank']})
csvfile.close()
