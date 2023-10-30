from setuptools import setup

setup(
    name='gp-reviews-tgrm-bot',
    packages=[
        'tgrmbot',
        'tgrmbot.googleplay',
        "twisted.plugins",
    ],
    package_data={'tgrmbot': ['templates/*.md',
                              'locales/en_US/LC_MESSAGES/messages.mo',
                              'locales/ru_RU/LC_MESSAGES/messages.mo']},
    zip_safe=False,
    include_package_data=True,
    version='0.3.2',

    url='https://github.com/3cky/gp-reviews-tgrm-bot',
    author='Victor Antonovich',
    author_email='victor@antonovich.me',
)

# Make Twisted regenerate the dropin.cache, if possible.  This is necessary
# because in a site-wide install, dropin.cache cannot be rewritten by
# normal users.
try:
    from twisted.plugin import IPlugin, getPlugins
except ImportError:
    pass
else:
    list(getPlugins(IPlugin))
