from typing import *
from .models import Variable as Varmodel, Command as Commodel, ListVariableItems
from login.models import AppUser
from random import randint

class Command:

    class Variable:
        def __init__(self, broadcaster, name, value):
            self.broadcaster = broadcaster
            self.name = name
            self.value = value
            self.broadcaster_obj = AppUser.objects.get(username=broadcaster)

        def __str__(self):
            return str(self.value)

        def setter(self, value):
            print(self.value, value)
            value = type(self.value)(value)
            print(value)
            try:
                self.value = value
                if type(value) != list:
                    variable = Varmodel.objects.get(broadcaster=self.broadcaster_obj, variable_name=self.name)
                    variable.variable_value = value
                    variable.save()
                else:
                    pass #should probably do something for list variables?
            except Exception as e:
                print(f"something went wrong with setting variable value: {e}")

        def __call__(self, *args, **kwargs):
            return self.value

    class IntVariable(Variable):
        def __init__(self, broadcaster, name, value):
            super().__init__(broadcaster, name, value)
            self.value = int(self.value)

        def __add__(self, other):
            return self.value + other

        def __mul__(self, other):
            return self.value * other

        def __truediv__(self, other):
            return self.value / other

        def __sub__(self, other):
            return self.value - other

        def add(self, number):
            number = int(number)
            try:
                self.value += number
                variable = Varmodel.objects.get(broadcaster=self.broadcaster_obj, variable_name=self.name)
                variable.variable_value = self.value
                variable.save()
            except Exception as e:
                print(f"something went wrong with adding to INT variable value: {e}")

    class ListVariable(Variable):
        def __init__(self, broadcaster, name, value):
            super().__init__(broadcaster,name,value)
            self.value = []
            self.variable_obj = Varmodel.objects.get(broadcaster=self.broadcaster_obj, variable_name=name)

            print("got to init method")
            for list_item in ListVariableItems.objects.filter(broadcaster=self.broadcaster_obj, variable_name=self.variable_obj):
                print(list_item.item_value)
                self.value.append(list_item.item_value)

        def clear(self):
            try:
                ListVariableItems.objects.filter(broadcaster=self.broadcaster_obj, variable_name=self.variable_obj,).delete()
                self.value = []
            except Exception as e:
                print(f"Something went wrong when clearing items: {e}")


        def add(self, item):
            try:
                ListVariableItems.objects.create(broadcaster=self.broadcaster_obj, variable_name=self.variable_obj, item_value=item)
                self.value.append(item)
            except Exception as e:
                print(f"Something went wrong when adding the item: {e}")

        def remove(self, item):
            try:
                ListVariableItems.objects.get(broadcaster=self.broadcaster_obj, variable_name=self.variable_obj, item_value=item).delete()
                self.value.pop(self.value.index(item))
            except Exception as e:
                print(f"Something went wrong when removing the item: {e}")


        @property
        def random(self):
            return self.value[randint(0,len(self.value)-1)]

    class StrVariable(Variable):
        def __init__(self, broadcaster, name, value):
            super().__init__(broadcaster, name, value)
            self.value = str(value)


    commands = {1:'ass', 2:'piss', 3:'fuck'}
    time_commands = {}

    def __call__(self, msg_json, mod=False,):
        message = msg_json['message']['text']
        chatter = msg_json['chatter_user_name']
        from commands.apps import CHATROOM_VARS, CHATROOM_COMS
        print("command was called")
        if not msg_json:
            print("you should pass the chat message and mod for the command")
        if self.mod and not mod:
            return "Plebs can't use this command."
        else:
            if self.function:
                try:
                    for x in self.function.split():
                        print(x)
                        exec(x ,{"__builtins__":{}, "var":CHATROOM_VARS[self.user.username], "chatter":chatter, "arg":message.split()})
                except Exception as hhghg:
                    print("something went wrong with executing function: {}".format(hhghg))
            if self.message:
                try:
                    return self.message.format(chatter=chatter, arg=message.split(), var=CHATROOM_VARS[self.user.username])
                except Exception as arggg:
                    print("something went wrong with sending message: {}".format(arggg))


    def __init__(self, user:str,  name: str, message: Optional[str] = None, function: Optional[str] = None, time: Optional[int] = None, mod: bool = False):
        """
        :param name: the name of the command, used to be stored in Command.commands dict
        :param message: message to be sent out to chat
        :param function: what the command does (for example increase self.counter, ban a person etc)
        :param time: if specified, the command will be called periodically every (self.time) seconds. (time) should be higher than 30.
        :param mod: if set to True, command will only be available to users with moderator status on the channel
        """
        self.user = user
        self.name = name
        self.raw_function = function #important for saving to the database and spares me the hassle of rewriting the Command class for the 4th time
        self.message = message if message else None
        self.function = function if function else None
        if time:
            self.time = time
            Command.time_commands[name] = self
        else: self.time = None
        self.mod = mod
        #Command.commands[name] = self

