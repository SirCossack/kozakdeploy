from django import forms
from commands.models import Command, Variable

class CommandForm(forms.ModelForm):
    class Meta:
        model = Command
        fields = ['command_name', "command_message", "command_function", "command_time", "command_mod"]

    command_name =  forms.CharField(widget=forms.Textarea(attrs={"class": "biginput","placeholder": "Enter command's name..."}))
    command_message = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "biginput", "placeholder": "Enter command's message..."}))
    command_function = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "biginput", "placeholder": "Enter command's function..."}))
    command_time = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={"class": "biginput","placeholder": "Enter interval in sec's..."}))
    command_mod = forms.BooleanField(required=False)

class VariableForm(forms.ModelForm):
    variable_value = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "biginput"}))
    class Meta:
        model = Variable
        fields = ['variable_name', 'variable_value', 'variable_type']
        widgets = {
            'variable_value': forms.Textarea(attrs={"class": "biginput"}),
            'variable_type': forms.Select(choices=[('str', "String"), ('int', "Integer"), ('list', "List")],
                                               attrs={'oninput': 'ShowItemVariables()'})}