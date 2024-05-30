# Slack Translate
Automatic Translation of Messages in Slack Example

This is a demonstration of how to build a Slack Bot that will automatically translate messages back and forth between two channels.

A much more detailed review of the design, configuration, and implementation be found in [https://mcguinnessai.substack.com](https://mcguinnessai.substack.com/p/chatting-in-the-global-village).

## Configuration

There are several steps involved in configuration the application to run, as you need to configure Slack, your hosting, and the application itself.

The first step is to fork this repository; that way, you are isolated from any breaking changes in the future.

### Hosting

The app includes a Procfile that should make it work with Heroku or Railway.app (I prefer Railway for many reasons, but either is fine).  You'll want to configure the hosting service to automatically pull from your forked copy of this repository.  

In theory (as in, I have not tested this), you should be able to run this for free on https://www.pythonanywhere.com.  Combined with Huggingface free API access, you could have a low-volume translation app in Slack for free.

When it's up and running you can move on to the next step:



### Slack Configuration

To configure Slack to use the application, here is a manifest you can use (the official copy is in slack-manifest.yml in this repository):

```
display_information:
  name: Translator
features:
  bot_user:
    display_name: Translator
    always_online: false
oauth_config:
  scopes:
    bot:
      - channels:history
      - incoming-webhook
      - users:read
settings:
  event_subscriptions:
    request_url: https://your-domain-here/events
    bot_events:
      - message.channels
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

Obviously, replace your-domain-here with your actual domain, like *foobar.herokuapp.com*.

Once you’ve updated the file, navigate to https://api.slack.com/apps. Press the green button that says “Create New App”. Then, pick “From an app manifest” from the pop-up window. Next, choose the workspace you want to install the app into and press Next.  You'll end up copying the manifest and pasting it into Slack to install the app.

When you install the app into your slack org, Slack will call the “events” URLto see if your app is alive and responsive. With some hosting services like Heroku, unfortunately, there’s every chance the app will be asleep and take too long to wake up to respond. So you may get a verification error. To fix that, on the left hand navigation for your app (in Slack api), find “Event Subscriptions” and click it. Now look to see if your URL is verified. If not, there’s a “Verify” button you can press. You may have to do it a couple of times[3](https://mcguinnessai.substack.com/p/getting-the-slack-translator-bot#footnote-3-137788186), but eventually it should be *Verified*.

You need to add two new webhooks, one for each of the two channels you are going to use (e.g., an "English" channel and a "Spanish" channel.). Save those URLs.

Finally, you'll need to "Add an App" to add your application.

### Configure the App

The application is driven by environment variables, which you set with your hosting service's UI.

| Key             | Value / Source                                               |
| --------------- | ------------------------------------------------------------ |
| BACKEND         | Set to either *HF* or *OpenAI* to pick whether you want to use Hugging Face and Llama3 or OpenAI.  See discussion below. |
| OPENAI_API_KEY  | Your key with OpenAI, if you are using it.  Not needed if you're using Hugging Face |
| HF_API_KEY      | Your key with Hugging Face, if you are using it.  Not needed if you're using OpenAI |
| SLACK_1_CHAN_ID | The channel ID of the first Slack Channel you are using      |
| SLACK_1_LANG    | The language (e.g., *US English*,  *Brazilian Portuguese*) spoken in the first channel |
| SLACK_2_CHAN_ID | The channel ID of the second Slack Channel you are using     |
| SLACK_2_LANG    | Language spoken in second channel                            |
| SLACK_TOKEN     | Found on Slack's OAuth & Permissions page as the Bot User OAuth Token |
| SLACK_VERIFY    | Found on Slack's Basic Information page as the Verification Token |



#### OpenAI vs Hugging Face

In theory, you can get a free account with Hugging Face and use it to do the translation instead of sending the traffic to OpenAI.  I've not tested it extensively, so consider it an experimental feature.  But it's free! 

If you set BACKEND to HF, it will use the Hugging Face API instead of OpenAI.  If you don't, it sticks with OpenAI.
