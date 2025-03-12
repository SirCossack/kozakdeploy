import requests
from django.apps import AppConfig
import time

class CommandsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'commands'

    def ready(self):
        import os
        import requests as rq
        import json
        import threading
        import websocket as ws
        ws.enableTrace(False)
        import time
        import login.models
        from commands.commands2 import Command as Com
        from commands.models import Command as ComModel, Variable as VarModel, ListVariableItems as VarItemsModel


        global get_user_id

        def checktoken():
            userurl = 'https://api.twitch.tv/helix/users?login=autokozak'
            userdata = json.loads(rq.get(userurl, headers={'Client-Id': os.getenv("client_id"),
                                                           'Authorization': 'Bearer {}'.format(
                                                               os.getenv('app_token'))}).text)
            print(userdata.get('status'))
            if userdata.get('status') == 401:
                print("apptoken invalid, getting a new one...")
                tokenresponse = requests.post("https://id.twitch.tv/oauth2/token",
                                      headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                      data={'client_id': os.getenv("client_id"),
                                          'client_secret': os.getenv('secret'),
                                          'grant_type': 'client_credentials'}).json()
                print(tokenresponse)
                token = tokenresponse['access_token']
                print("token: ", token)
                os.environ['app_token'] = token
                print("apptoken updated!")
            elif userdata.get('status') == 200:
                print("apptoken valid!")

        def get_user_id(user: str) -> str:
            """
            Gets twitch user ID as a string
            :param user: (str) a twitch username that you want to know the ID of
            :return: (str) user ID
            """
            userurl = 'https://api.twitch.tv/helix/users?login={}'.format(user)
            userdata = json.loads(rq.get(userurl, headers={'Client-Id': os.getenv("client_id"),
                                                'Authorization': 'Bearer {}'.format(os.getenv('app_token'))}).text)

            if userdata.get('status') == 401: #This is usually where access tokens are a problem
                print("your dumb ass has old tokens")

            return userdata['data'][0]['id']

        def send_message(channel: str, message: str):
            """
            Sends a message to a twitch channel's chat
            :param channel: the channel name you wish to send a message to
            :param message: the message you wish to send
            :return: None
            """
            print("mesage in send_message func:", message)
            print(rq.post('https://api.twitch.tv/helix/chat/messages',
                    headers={'Client-Id': os.getenv("client_id"),
                             'Authorization': 'Bearer {}'.format(os.getenv('user_token')),
                             'Content-type': 'application/json'},
                    data=json.dumps({'broadcaster_id': '{}'.format(get_user_id(channel)),
                                     'sender_id': '{}'.format(get_user_id(os.getenv('username'))),
                                     'message': '{}'.format(message)})))

        def _onmessage(wsapp: ws.WebSocketApp, message) -> None:
            """
            Function reacts to websocket messages that occur during connection.
            :param wsapp: (object) the websocket connection that the messages are coming from
            :param message: (object) The websocket message
            :return:
            """
            #print(message)
            if json.loads(message)['metadata']['message_type'] == 'notification':
                chat_broadcaster = json.loads(message)['payload']['event']['broadcaster_user_login']
                chat_message = json.loads(message)['payload']['event']['message']['text']
                print(chat_message)
                if chat_message.startswith("!"):
                    mod = False
                    for i in json.loads(message)['payload']['event']['badges']:
                        if i.get('set_id') == 'moderator' or i.get('set_id') == 'broadcaster':
                            mod = True
                            break
                    commandname = chat_message.split()[0][1:]

                    if CHATROOM_COMS[chat_broadcaster].get(commandname):
                        send_message(chat_broadcaster, CHATROOM_COMS[chat_broadcaster][commandname](json.loads(message)['payload']['event'], mod))

            if json.loads(message)['metadata']['message_type'] == 'session_welcome':
                global SESSION_ID
                SESSION_ID = json.loads(message)['payload']['session']['id']
                BOT_ID = get_user_id(os.getenv('username'))

                for channel in login.models.AppUser.objects.all():
                    CHATROOM_COMS[channel.username] = {}
                    CHATROOM_VARS[channel.username] = {}

                    for com in ComModel.objects.filter(broadcaster=channel):
                        CHATROOM_COMS[channel.username][com.command_name] = Com(user=com.broadcaster,
                                                                                name=com.command_name,
                                                                                message=com.command_message,
                                                                                function=com.command_function,
                                                                                time=com.command_time,
                                                                                mod=com.command_mod)

                    for var in VarModel.objects.filter(broadcaster=channel):
                        if var.variable_type == 'int':
                            CHATROOM_VARS[channel.username][var.variable_name] = Com.IntVariable(channel.username,
                                                                                                 var.variable_name,
                                                                                                 var.variable_value)
                        elif var.variable_type == "str":
                            CHATROOM_VARS[channel.username][var.variable_name] = Com.StrVariable(channel.username,
                                                                                                 var.variable_name,
                                                                                                 var.variable_value)
                        elif var.variable_type == 'list':
                            CHATROOM_VARS[channel.username][var.variable_name] = Com.ListVariable(channel.username,
                                                                                                  var.variable_name,
                                                                                                  [])

                    if channel.bot_active == 1:
                        dataforrequest = json.dumps({
                        'type': 'channel.chat.message',
                        'version': '1',
                        "condition": {
                            "broadcaster_user_id": get_user_id(channel),
                            "user_id": BOT_ID},
                        'transport': {
                            "method": "websocket",
                            "session_id": SESSION_ID}})

                        subscription = json.loads(rq.post('https://api.twitch.tv/helix/eventsub/subscriptions',
                                      headers={'Client-Id': os.getenv("client_id"),
                                               'Authorization': 'Bearer {}'.format(os.getenv('user_token')),
                                               'Content-type': 'application/json'}, data=dataforrequest).text)
                        CHATROOM_SUBS[channel.username] = subscription['data'][0]['id']


                        send_message(channel.username, "AutoKozak is here!")

        global CHATROOM_SUBS
        CHATROOM_SUBS = {}
        global CHATROOM_COMS
        CHATROOM_COMS = {}
        global CHATROOM_VARS
        CHATROOM_VARS = {}

        def run_bot():
            #checktoken()
            authheaders = {'Client-Id': os.getenv("client_id"), 'Authorization': 'Bearer {}'.format(os.getenv('app_token'))}
            socket = ws.WebSocketApp("wss://eventsub.wss.twitch.tv/ws", header=authheaders, on_message=_onmessage,)
            socket.run_forever(sslopt={'username': os.getenv('username'),
                                       'password': 'oauth:{}'.format(os.getenv('app_token')),
                                       'channels': os.getenv('channel')})

        bot_thread = threading.Thread(name="bot_thread", target=run_bot)
        bot_thread.start()
        time.sleep(1)