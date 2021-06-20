import requests
import json
from datetime import datetime
from typing import Dict


guest_token: str = ''
guest_token_last_update_time: datetime = None


def is_twitter_url(url: str) -> bool:
    return url.find('twitter.com') != -1


def add_twitter_guest_token_if_twitter(url: str, headers: Dict):
    if not is_twitter_url(url):
        return
    headers['x-guest-token'] = _get_twitter_guest_token()


def get_denormalized_tweet_dict(twitter_response: str) -> Dict:
    twitter_response_dict = json.loads(twitter_response)
    twitter_response_dict = _fill_full_user_name_fields_in_tweet_object(twitter_response_dict)
    return twitter_response_dict


def add_tweet_url_to_tweets(twitter_response_dict: Dict) -> Dict:
    for tweet in twitter_response_dict['globalObjects']['tweets'].values():
        tweet['tweet_url'] = 'https://twitter.com/' + tweet['user_screen_name'] + '/status/' + tweet['id_str']
    return twitter_response_dict


def _get_twitter_guest_token():
    global guest_token
    global guest_token_last_update_time

    if guest_token:
        if (datetime.now() - guest_token_last_update_time).total_seconds() < 60 * 60:
            return guest_token
        else:
            guest_token_last_update_time = None
            guest_token = ''

    headers = {
        'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xn' +
                         'Zz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'User-Agent': 'PostmanRuntime/7.28.0'
    }
    activate_response = requests.post('https://api.twitter.com/1.1/guest/activate.json', headers=headers)

    if activate_response.status_code == 200:
        guest_token_dict = json.loads(activate_response.text)
        guest_token = guest_token_dict['guest_token']
        guest_token_last_update_time = datetime.now()

    return guest_token


def _fill_full_user_name_fields_in_tweet_object(twitter_response_dict: Dict) -> Dict:
    tweets_dict = twitter_response_dict['globalObjects']['tweets']
    users_dict = twitter_response_dict['globalObjects']['users']
    for tweet in tweets_dict.values():
        user_id_str = tweet['user_id_str']
        tweet['user_name'] = users_dict[user_id_str]['name']
        tweet['user_screen_name'] = users_dict[user_id_str]['screen_name']
    return twitter_response_dict
