# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Django
from django import forms

# Zato
from zato.common import PROCESS

class CreateForm(forms.Form):
    id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(widget=forms.TextInput(attrs={'style':'width:100%'}))
    is_active = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'checked':'checked'}))
    lang_code = forms.ChoiceField(widget=forms.Select())
    text = forms.CharField(initial=PROCESS.DEFAULT.en_uk, widget=forms.Textarea(
        attrs={'style':'width:100%; height:400px', 'class':'required'}))

    def __init__(self, prefix=None, post_data=None):
        super(CreateForm, self).__init__(post_data, prefix=prefix)

        self.fields['lang_code'].choices[:] = []

        for name, value in PROCESS.LANGUAGE.iteritems():
            self.fields['lang_code'].choices.append([value.value, name])

class EditForm(CreateForm):
    is_active = forms.BooleanField(required=False, widget=forms.CheckboxInput())
