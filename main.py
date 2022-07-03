import sys
import json
import time
import random
from datetime import datetime, timedelta, timezone
import tweepy

cooldown_interval = [5, 25]

def read_secrets(file):
    f = open(file, 'r')
    secrets = json.loads(f.read())
    print(secrets)
    return secrets

def get_tweeAPI(secrets):
    apis = []
    for secret in secrets:
        print(secret['API_key'], secret['API_secret'], secret['access_token'], secret['access_token_secret'])
        auth = tweepy.OAuthHandler(secret['API_key'], secret['API_secret'])
        auth.set_access_token(secret['access_token'], secret['access_token_secret'])
        api = tweepy.API(auth)
        apis.append(api)
    return apis

def register_raffle(apis, project):
    query = f"{project} giveaway filter:replies OR -filter:retweet"

    for api in apis:
        tweets = api.search_tweets(query, result_type="recent", count=10)

        for tweet in tweets:
            # TODO: check if the tweet is a retweet or not
            # if hasattr(tweet, 'retweeted_status'):
            #     continue
            print('=========================================================================')
            create_time = tweet.created_at
            now = datetime.now(timezone.utc)
            if now - create_time > timedelta(hours=23, minutes=30):
                continue
            
            tweet_id = str(tweet.id)
            full_text = tweet.text.encode("utf8").decode("cp950", "ignore")

            print(tweet_id)
            print(full_text)

            author = tweet.author.screen_name
            print(f'author: {author}')

            if not api.get_status(tweet_id).favorited:
                api.create_favorite(id=tweet_id)
            if not api.get_status(tweet_id).retweeted:
                api.retweet(id=tweet_id)
            follow_mentioned_accounts(api, full_text)
            tag_friends(api, tweet_id, 3)

            # cool down
            time.sleep(random.randint(cooldown_interval[0], cooldown_interval[1]))
            


def tag_friends(api, tweet_id, cnt):
    friends = api.get_friends()
    comment = ''
    for i in range(cnt):
        idx = random.randint(i, (i+1)*(len(friends)//cnt))
        comment += ('@' + friends[idx].screen_name + ' ')
    print(f'comment: {comment}')
    api.update_status(comment, in_reply_to_status_id=tweet_id, auto_populate_reply_metadata=True)
     

def follow_mentioned_accounts(api, full_text):
    to_follows = set()

    idx = 0
    marks = [' ', ',', ';', ':', '\n', '...', '\\']
    while idx != -1:
        tmp_idx = full_text.find('@', idx)
        mark_ids = [full_text.find(x, tmp_idx) for x in marks] 
        idx_found = list(filter(lambda x: x != -1, mark_ids))

        if not idx_found:
            idx = -1
            to_follows.add(full_text[tmp_idx:])
        else:
            idx = min(idx_found)
            to_follows.add(full_text[tmp_idx:idx])
    print(f'mentioned accounts: {to_follows}')
    
    for f in to_follows:
        api.create_friendship(screen_name=f)    
    

def main():
    random.seed(datetime.now())
    if len(sys.argv) != 2:
        print('usage: python3 main.py project_name')
        return -1
    secrets = read_secrets('secret.json')
    apis = get_tweeAPI(secrets)
    print(f'project: {str(sys.argv[1])}')
    register_raffle(apis, str(sys.argv[1]))

    
if __name__ == '__main__':
    main()
