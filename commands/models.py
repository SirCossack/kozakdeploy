from django.db import models

import login.models


# Create your models here.

class Command(models.Model):
    broadcaster = models.ForeignKey("login.AppUser", models.CASCADE,)
    command_name = models.CharField(max_length=50)
    command_message = models.TextField(blank=True)
    command_function = models.TextField(blank=True)
    command_time = models.IntegerField(blank=True)
    command_mod = models.BooleanField(default=False)


class Variable(models.Model):
    broadcaster = models.ForeignKey("login.AppUser", models.CASCADE,)
    variable_name = models.CharField(max_length=50)
    variable_type = models.CharField(max_length=50)
    variable_value = models.CharField(max_length=512, blank=True)

class ListVariableItems(models.Model):
    broadcaster = models.ForeignKey("login.AppUser", models.CASCADE, )
    variable_name = models.ForeignKey("commands.Variable", models.CASCADE,) #It's actually variable_id and not variable name
    item_value = models.CharField(max_length=500)