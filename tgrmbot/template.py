# -*- coding: utf-8 -*-
'''
Created on 22-Feb-2017

@author: 3cky
'''

from jinja2 import Environment, PackageLoader

from tgrmbot.util import format_datetime, format_timedelta


class TemplateRenderer(object):
    '''
    Template renderer.

    '''

    def __init__(self, l10n_support):
        templateLoader = PackageLoader('tgrmbot', 'templates')
        self.templateEnvironment = Environment(loader=templateLoader,
                                               extensions=['jinja2.ext.i18n'])
        self.templateEnvironment.install_gettext_translations(l10n_support.get_translations())
        self.templateEnvironment.globals['locale'] = l10n_support.locale
        self.templateEnvironment.filters['datetime'] = format_datetime
        self.templateEnvironment.filters['timedelta'] = format_timedelta

    def render(self, templateName, *args, **kwargs):
        template = self.templateEnvironment.get_template(templateName)
        return template.render(*args, **kwargs)
