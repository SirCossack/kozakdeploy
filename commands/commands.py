"""
var[eggs].add(1)
com[ban]({xavierasty})












"""





"""
Place where I'll hopefully be able to store bot commands


TO DO:
-command counters can't get reset on restarting the bot (database?)
-multiple channels should have the same command but different counts (database?)

"""
from typing import *
import mysql.connector as sql
import authconfig
import json


class Command:
    @staticmethod
    def add(mod:bool , message:str) -> str:
        """
        A command to add another commands in chat. I hate it slightly less than the first implementation.
        The input string format:

            "!add (command_name) (integer_variable_name)=(variable_value) (string_variable.name)='(string_variable_value)' (list_variable_name)=[(item1),(item2),(item3)...]"

            The command supports addition of 3 specific variables (message, function and time) as well custom variables like counters.
            message: [str] - specifies the message to be sent to Twitch chatroom by the bot
            function: [str] - operation in code, like increasing counters or editing values
            time: [int] - if specified, the command will be called every (time) seconds. Should be at least 30.

        Example:
            "!add deathcount message='The streamer has died {count} times.' function='{count} = {count} + 1' count=0"

        :param mod: param specyfing if the user calling the command has moderator access
        :param message: The message from chat the bot will receive
        :return: a string saying weather a command was successfully created
        """
        if not mod:
            return "This command is reserved for users with moderator access"

        params = message.split()
        name = params[1]
        if Command.commands.get(name):
            return "Command !{} alredy exists.".format(name)
        message = None
        function = None
        time = None
        kwargs = {}
        i=2
        while i < len(params):
            if params[i].startswith('message='):
                message = params[i][8:]
                i += 1
                if message.endswith(("'",'"')):
                    continue
                while i < len(params):
                    message = message + ' ' + params[i]
                    if "'" in params[i] or '"' in params[i]:
                        break
                    i += 1

            elif params[i].startswith('function='):
                function = params[i][9:]
                i = i + 1
                if function.endswith(("'", '"')):
                    continue
                while i < len(params):
                    function = function + ' ' + params[i]
                    if "'" in params[i] or '"' in params[i]:
                        break
                    i += 1

            elif params[i].startswith('time='):
                time = int(params[i][5:])
                if time < 30:
                    return "Cannot add command - time should be at least 30s"

            elif "=" in params[i]:
                key = params[i][:params[i].index("=")]
                value = params[i][1+params[i].index("="):]
                i += 1
                while i < len(params) and '=' not in params[i]:
                    value += " " + params[i]
                    i += 1
                kwargs[key] = value
                i -= 1
            i += 1
        try:
            Command(name, message, function, time, **kwargs)
            return "Command '{}' added.".format(name)
        except Exception: #placeholder since i don't yet know what errors to expect
            raise Exception

    @staticmethod
    def delete(mod:bool , message:str) -> str:
        """
        Command to delete other commands.
        The input string format:
            !del (command.name)

        :param mod: param specyfing if the user calling the command has moderator access
        :param message: The message from chat the bot will receive
        :return: a string saying weather a command was successfully created"""

        if not mod:
            return "This command is reserved for users with moderator access"

        if message.split()[1] == 'add' or message.split()[1] == 'del':
            return "Command cannot be deleted."

        else:
            del Command.commands[message.split()[1]]
            return "Command deleted successfully"

    def __call__(self, mod, *args):
        if self.mod and not mod:
            return "This command is reserved for users with moderator access"
        else:
            if self.function: exec(self.function(*args),{"__builtins__": {}, "Command":Command, "Command.commands":Command.commands},{"self":self})
            if self.message: return self._parse("message", self.message.strip("'"))(*args)

    def save(self, mysql_cursor):
        """
        Saves the state of a command to the database
        :param mysql_cursor: cursor connected to the database
        :return: None
        """
        try:
            mysql_cursor.execute('SELECT broadcaster_name FROM broadcaster WHERE broadcaster_name = %s', (authconfig.channel,))
            next(mysql_cursor)
        except StopIteration:
            mysql_cursor.execute("INSERT INTO broadcaster (broadcaster_name) VALUES (%s)", (authconfig.channel,))

        mysql_cursor.execute('SELECT broadcaster_id FROM broadcaster WHERE broadcaster_name = %s', (authconfig.channel,))
        broadcaster_id = next(mysql_cursor)['broadcaster_id']
        mysql_cursor.execute('SELECT command_name FROM command WHERE command_name = %s', (self.name,))
        parameters = {self.param_names[i]:eval("self.{}".format(self.param_names[i])) for i in range(len(self.param_names))}
        try:
            next(mysql_cursor)
            mysql_cursor.execute(
                'UPDATE command SET command_message = %s, command_function = %s, command_time = %s, command_mod = %s, command_custom = %s WHERE (command_name = %s AND broadcaster_id = %s)',
                (self.message, self.raw_function, self.time, self.mod, json.dumps(parameters), self.name,
                 broadcaster_id))
        except StopIteration:
            mysql_cursor.execute(
                'INSERT INTO command (broadcaster_id, command_name, command_message, command_function, command_time, command_mod, command_custom) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (broadcaster_id, self.name, self.message, self.raw_function, self.time, self.mod,
                 json.dumps(parameters)))

    def _parse(self, type: str, message: str) -> Callable:
        """
        Takes self.function/self.message from the Command object and converts it from unparsed state (for example: '{count} = {count} + 1.) to a function returning a parsed string ('self.count = self.count + 1.)
        Also changes 'xxxxx.count' into 'Command.commands['xxxxx'].count, so variables from other commands are also available.
        Also changes '{#1}', '{#2}', '{#3}'... into arguments that will be passed to a returned function
        :param type: determines whether to return message or function, since they need slightly different formatting. Should be either "message" or "function"
        :param message: self.message or self.function
        :return: a function returning a parsed string
        """
        output = ''
        bracket = False
        variables = []
        arguments = []
        for char in message:
            if bracket:
                if char == '}':
                    bracket = False
                    variables.append(variable)
                    output += char
                else:
                    variable += char
                continue

            if char == '{':
                bracket = True
                variable = ''
                output += char

            else:
                output += char

        for i in range(len(variables)):
            if "." in variables[i]:
                idx = variables[i].index(".")
                variables[i] = "Command.commands['{}'].{}".format(variables[i][:idx], variables[i][idx+1:])
            elif "#" in variables[i]:
                arguments.append(int(variables[i][1:]))
                variables[i] = "{}"
            else:
                variables[i] = "self." + variables[i]

        if type == "message":
            output = output.format(*[eval(i, {"__builtins":{}}, {"self": self}) for i in variables])
        if type == "function":
            output = output.format(*[i for i in variables])


        if arguments:
            def a(*chat_message):
                chat_message = chat_message[0].split()
                return output.format(*(chat_message[i] for i in arguments))
        else:
            def a(*chat_message):
                return output
        return a

    commands = {'add':add, 'del':delete}
    time_commands = {}
    _new = {}

    def __init__(self, name: str, message: Optional[str] = None, function: Optional[str] = None, time: Optional[int] = None, mod: bool = False, **params):
        """
        :param name: the name of the command, used to be stored in Command.commands dict
        :param message: message to be sent out to chat
        :param function: what the command does (for example increase self.counter, ban a person etc)
        :param time: if specified, the command will be called periodically every (self.time) seconds. (time) should be higher than 30.
        :param mod: if set to True, command will only be available to users with moderator status on the channel
        """
        self.name = name
        self.raw_function = function #important for saving to the database and spares me the hassle of rewriting the Command class for the 4th time
        self.param_names = []
        for key, value in params.items():
            exec("self.{} = {}".format(key,value), {"__builtins__":{}}, {'self': self})
            self.param_names.append(key)
        if message: self.message = message
        else: self.message = ""
        if function: self.function = self._parse("function", function.strip("'"))
        else: self.function = ""
        if time:
            self.time = time
            Command.time_commands[name] = self
        else: self.time = None
        self.mod = mod
        Command.commands[name] = self


