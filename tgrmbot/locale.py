'''
Created on 24-Feb-2017

@author: 3cky
'''

from gettext import translation
import babel.support
import pkg_resources

LOCALES = ['en_US', 'ru_RU']

class LocalizationSupport(object):
    '''
    Localization support.

    '''

    def __init__(self, lang):
        self.locale = self.to_locale(lang)
        locale_dir = pkg_resources.resource_filename('tgrmbot', 'locales')
        self.translations = babel.support.Translations.load(dirname=locale_dir,
                                                            locales=[self.locale])
        t = translation('messages', localedir=locale_dir, languages=[self.locale])
        t.install()


    def get_locales(self):
        return LOCALES


    def get_locale(self):
        return self.locale


    def to_locale(self, lang):
        for l in self.get_locales():
            if l.startswith(lang):
                return l
        return None


    def get_translations(self):
        return self.translations
