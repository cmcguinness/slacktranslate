"""
    SlackWrapper

    This handles the incoming message events from Slack by:

    1.  Determining if we need to translate the message
    2.  Converting user ids in the message to names
    3.  Sending the text out to get translated
    4.  Posting the translated text into the "other" channel

"""
import os
import requests
import json
from openaiwrapper import OpenAIWrapper
from threading import Thread

class SlackWrapper:

    #   Init is responsible for fetching the environment variables that have
    #   API keys, endpoints, and channel ids for our particular org
    def __init__(self):
        self.channel_1_id = os.getenv('SLACK_1_CHAN_ID')
        self.channel_1_lang = os.getenv('SLACK_1_LANG')
        self.channel_2_id = os.getenv('SLACK_2_CHAN_ID')
        self.channel_2_lang = os.getenv('SLACK_2_LANG')
        self.slack_token = os.getenv('SLACK_TOKEN')
        self.slack_verification = os.getenv('SLACK_VERIFY')


    # Lookup a user's name from their id
    def get_user_name_image(self, id:str):
        payload = {'token': self.slack_token, 'user': id}
        print(self.slack_token[:10], flush=True)
        resp = requests.post('https://slack.com/api/users.info', data=payload)
        print(resp.text, flush=True)
        data = json.loads(resp.content)
        if 'error' in data:
            print(f'get_user_name({id}): Error {data["error"]}', flush=True)
        if 'user' not in data:
            return '-unknown-', ''

        name = '-unknown-'
        image = ''

        if 'name' in data['user']:
            name = data['user']['name']

        if 'profile' in data['user']:
            profile = data['user']['profile']
            if 'display_name' in profile:
                name = profile['display_name']

            if 'image_original' in profile:
                image = profile['image_original']
            if 'image_48' in profile:
                image = profile['image_48']

        return name, image

    def get_user_name(self, id:str):
        name, image = self.get_user_name_image(id)
        return name


    # Take a line of text with 0 or more embedded <@id> in it and expand the
    # ids to user names
    def expand_users(self, text):
        result = ''

        while (loc := text.find('<@')) != -1:
            result = result + text[:loc] + '@'
            text = text[loc + 2:]
            end = text.find('>')
            if end == -1:
                break

            user_id = text[:end]
            text = text[end + 1:]
            user_name = self.get_user_name(user_id)
            result = result + user_name

        result = result + text
        return result

    def post_text2(self, channel, text, user=None, image=None):
        payload = {'token': self.slack_token, 'text': text, 'channel': channel}

        if user is not None:
            payload['username'] = user

        if image is not None and image != '':
            payload['icon_url'] = image

        r = requests.post('https://slack.com/api/chat.postMessage', data=payload)
        print('postMessage: ',r.status_code, flush=True)
        print(r.text, flush=True)

        return r  # Not that anyone cares...

    # This runs in the background so we can respond to slack quickly
    def do_translate(self, to_lang, text, user, dest_channel):
        text = self.expand_users(text)

        image = None

        if user is not None:
            user, image = self.get_user_name_image(user)

        oai = OpenAIWrapper()

        new_text = oai.to_language(to_lang, text)

        if new_text is None:
            print('Translation failure!', flush=True)
            return

        self.post_text2(dest_channel, new_text, user, image)

    # Handle an event notification from slack
    # Because the call to open
    def handle_event(self, event):

        c = event['channel']

        # We may get a lot more traffic than we'd like, so make sure
        # it's coming from the channels we're interested in
        if c not in [self.channel_1_id, self.channel_2_id]:
            return ''

        # Filter out non-user messages
        if 'user' not in event:
            # system message
            return ''

        # Filter out bot messages (like ours) posing as users
        if 'bot_id' in event:
            return ''

        # Make sure there's something to translate
        if 'text' not in event or len(event['text'].strip()) == 0:
            return ''

        to_language = [self.channel_1_lang, self.channel_2_lang][c != self.channel_2_id]
        to_channel =  [self.channel_1_id, self.channel_2_id][c != self.channel_2_id]

        th = Thread(target=self.do_translate, args=(to_language, event['text'], event['user'], to_channel))
        th.start()
        return ''



