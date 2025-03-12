from time import sleep
sleep(0.25)
from django.shortcuts import render, reverse
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from .models import AppUser
from commands.models import Command, Variable, ListVariableItems
from django.contrib.auth import login, logout
from login.forms import CommandForm, VariableForm
import requests
import os
from commands.apps import CHATROOM_SUBS, SESSION_ID, get_user_id, CHATROOM_COMS, CHATROOM_VARS
from commands.commands2 import Command as Com
import json


def logged_in(request):
    if not request.user.is_authenticated:
        return render(request, 'loginpage.html', )
    else:
        print(request.user, request.user.uid)
        usercommands = Command.objects.filter(broadcaster=request.user)
        uservars = Variable.objects.filter(broadcaster=request.user)
        filled_command_forms = []
        for i in usercommands:
            filled_command_forms.append(CommandForm(instance=i))
        filled_variable_forms = []
        for i in uservars:
            filled_variable_forms.append(VariableForm(instance=i))
        return render(request, 'mainpage.html', {"user": AppUser.objects.filter(username=request.user)[0],
                                                 "usercommands": usercommands,
                                                 "uservars": uservars,
                                                 "usercommandforms": filled_command_forms,
                                                 "uservariableforms": filled_variable_forms,
                                                 "commandform": CommandForm(auto_id="$s"),
                                                 "variableform": VariableForm()})


def add_command(request):
    form = CommandForm(auto_id="$s")
    if request.GET.get('command'):
        com = Command.objects.get(broadcaster=request.user, command_name=request.GET['command'])
        form = CommandForm(instance=com, auto_id="$s")
    coms = Com.commands.values()
    variables = CHATROOM_VARS[request.user.username]
    varcoms = None
    return render(request, 'addcommand.html', {"form": form, "coms":coms,
                                               "vars": variables, "varcoms": varcoms})

def add_variable(request):
    form = VariableForm
    items = []
    if request.GET.get('variable'):
        print(request.GET)
        var = Variable.objects.get(broadcaster=request.user, variable_name=request.GET['variable'])
        if var.variable_type == "list":
            items = ListVariableItems.objects.filter(broadcaster=request.user, variable_name=var)
        form = VariableForm(instance=var)
    return render(request, 'addvariable.html', {"form": form, "var_items":items})


def add_command_form(request): #do something with update_or_create
    print(request.POST)
    print("request user username", request.user.username, type(request.user.username)) #str

    addcomand = Command.objects.update_or_create(broadcaster=request.user,
                                       command_name=request.POST['command_name'],
                                                 defaults={"command_message": request.POST['command_message'],
                                                           "command_function": request.POST['command_function'],
                                                           "command_time": 0 if not request.POST['command_time'] else request.POST['command_time'],
                                                           "command_mod": False if not request.POST.get('command_mod') else True})
    addcomand[0].save()
    CHATROOM_COMS[request.user.username][request.POST['command_name']] = Com(user=request.user,
                                                                    name=request.POST['command_name'],
                                                                    message=request.POST['command_message'],
                                                                    function=request.POST['command_function'],
                                                                    time=0 if not request.POST['command_time'] else request.POST['command_time'],
                                                                    mod=False if not request.POST.get('command_mod') else True)
    return HttpResponse("thx")

def add_variable_form(request): #do something with update_or_create
    print(request.POST)
    addvar = Variable.objects.update_or_create(broadcaster=request.user,
                                       variable_name=request.POST['variable_name'],
                                               defaults={"variable_type":request.POST['variable_type'],
                                                         "variable_value":request.POST['variable_value']})
    addvar[0].save()

    if request.POST['variable_type'] == 'int':
        CHATROOM_VARS[request.user.username][request.POST['variable_name']] = Com.IntVariable(request.user,
                                                                             request.POST['variable_name'],
                                                                             request.POST['variable_value'])
    elif request.POST['variable_type'] == "str":
        CHATROOM_VARS[request.user.username][request.POST['variable_name']] = Com.StrVariable(request.user,
                                                                                     request.POST['variable_name'],
                                                                                     request.POST['variable_value'])
    elif request.POST['variable_type'] == 'list':
        variable_obj = Variable.objects.get(broadcaster=request.user, variable_name=request.POST['variable_name'])
        ListVariableItems.objects.filter(broadcaster=request.user, variable_name=variable_obj).delete()
        for i in request.POST.getlist('listvarelements'):
            if not i:
                continue
            ListVariableItems.objects.create(broadcaster=request.user,
                                             variable_name=variable_obj,
                                             item_value=i)

        x = Com.ListVariable(request.user, request.POST['variable_name'], [])
        CHATROOM_VARS[request.user.username][request.POST['variable_name']] = x
    return HttpResponse("thx")

def log_out(request):
    logout(request)
    return HttpResponseRedirect(reverse('home'))

def activate_bot(request):
    user = AppUser.objects.get(username=request.user.username)
    print(CHATROOM_SUBS)
    if user.bot_active:
        requests.delete('https://api.twitch.tv/helix/eventsub/subscriptions?id={}'.format(CHATROOM_SUBS[user.username]),
                         headers={'Client-Id': os.getenv('client_id'),
                                  'Authorization': 'Bearer {}'.format(os.getenv('user_token'))})
        user.bot_active = 0
        user.save()
        return HttpResponseRedirect(reverse('home', args=()))

    else:
        subtochat = requests.post('https://api.twitch.tv/helix/eventsub/subscriptions',
                    headers={'Client-Id': os.getenv('client_id'),
                             'Authorization': 'Bearer {}'.format(os.getenv('user_token')),
                             'Content-type': 'application/json'},
                    data=json.dumps({
                             'type': 'channel.chat.message',
                             'version': '1',
                             "condition": {
                                 "broadcaster_user_id": get_user_id(user.username),
                                 "user_id": get_user_id(os.getenv('username'))},
                             'transport': {
                                 "method": "websocket",
                                 "session_id": SESSION_ID}}))
        print(subtochat.text) #add logic when response != 200

        CHATROOM_SUBS[user.username] = json.loads(subtochat.text)['data'][0]['id']
        user.bot_active = 1
        user.save()
        return HttpResponseRedirect(reverse('home', args=()))

def delete_command(request):
    Command.objects.filter(command_name=request.GET['command']).delete()
    return HttpResponse('deleted')

def delete_variable(request):
    Variable.objects.filter(variable_name=request.GET['variable']).delete()
    return HttpResponse('deleted')

def wtfisclick(request):
    print("Click!")
    return JsonResponse({"clicked":"clicked."})

