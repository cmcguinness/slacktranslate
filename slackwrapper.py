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
from dbtools import DBTools

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
        # print(resp.text, flush=True)
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

    def post_text(self, channel, text, user, image, files, thread_ts, source_ts):
        db = DBTools()

        if files is not None:
            text += '\n\n'
            for f in files:
                if 'permalink' in f and 'name' in f:
                    text = text + f"<{f['permalink']} | {f['name']}>"

        payload = {'token': self.slack_token, 'text': text, 'channel': channel}

        if thread_ts is not None:
            trans_thread_ts = db.source_to_trans(thread_ts)
            print(f'source_to_trans({thread_ts}) = {trans_thread_ts}', flush=True)
            if trans_thread_ts is None:
                text = '(_Reply_): ' + text
            else:
                payload['thread_ts'] = trans_thread_ts

        if user is not None:
            payload['username'] = user

        if image is not None and image != '':
            payload['icon_url'] = image

        print(payload['text'])
        print('---', flush=True)

        r = requests.post('https://slack.com/api/chat.postMessage', data=payload)

        resp = r.json()

        db.add_post(source_ts, resp['ts'])

    # This runs in the background so we can respond to slack quickly
    def do_translate(self, to_lang, text, user, dest_channel, files,  thread_ts, source_ts):
        text = self.expand_users(text)

        image = None

        if user is not None:
            user, image = self.get_user_name_image(user)

        oai = OpenAIWrapper()

        new_text = oai.to_language(to_lang, text)

        if new_text is None:
            print('Translation failure!', flush=True)
            return

        self.post_text(dest_channel, new_text, user, image, files, thread_ts, source_ts)

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

        # Filter out channel join messages
        if 'subtype' in event and event['subtype'] == 'channel_join':
            return ''

        # Make sure there's something to translate
        if 'text' not in event or len(event['text'].strip()) == 0:
            return ''

        files = None
        if 'files' in event:
            files = event['files']

        thread_ts = None
        if 'thread_ts' in event:
            thread_ts = event['thread_ts']

        source_ts = event['ts']


        to_language = [self.channel_1_lang, self.channel_2_lang][c != self.channel_2_id]
        to_channel =  [self.channel_1_id, self.channel_2_id][c != self.channel_2_id]

        th = Thread(target=self.do_translate, args=(to_language, event['text'], event['user'], to_channel, files,  thread_ts, source_ts))
        th.start()
        return ''



