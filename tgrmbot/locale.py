'''
Created on 24-Feb-2017

@author: 3cky
'''

from contextlib import contextmanager

import locale

import babel.support

import pkg_resources

LOCALES = ['en_US', 'ru_RU']

class LocalizationSupport(object):
    '''
    Localization support.

    '''

    def __init__(self, default_lang):
        self.default_lang = default_lang
        localeDir = pkg_resources.resource_filename('tgrmbot', 'locales')
        self.translations = babel.support.Translations.load(dirname=localeDir, locales=LOCALES)


    def get_locales(self):
        return LOCALES


    def get_translations(self):
        return self.translations


    @contextmanager
    def set_locale(self, l):
        """
        Temporarily overrides the currently set locale.
        :param l: The locale to temporary switch to (ex: 'en_US').
        """
        orig_locale = locale.getlocale()
        try:
            locale.setlocale(locale.LC_ALL, l)
            yield
        finally:
            locale.setlocale(locale.LC_ALL, orig_locale)