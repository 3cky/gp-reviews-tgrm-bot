# -*- coding: utf-8 -*-
'''
Created on 20-Feb-2017

@author: 3cky
'''

from twisted.enterprise import adbapi
from twisted.internet import defer


class DataStorage(object):
    '''
    Bot data persistent storage.

    '''

    def __init__(self, db_filename):
        # open database
        self._dbpool = adbapi.ConnectionPool("sqlite3", db_filename, check_same_thread=False)
        self._create_tables()

    @defer.inlineCallbacks
    def _create_tables(self):
        # create apps table
        yield self._dbpool.runQuery(
            'CREATE TABLE IF NOT EXISTS apps ' +
            '(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, desc TEXT)')
        # create reviews table
        yield self._dbpool.runQuery(
            'CREATE TABLE IF NOT EXISTS reviews ' +
            '(id INTEGER PRIMARY KEY AUTOINCREMENT, app_id INTEGER, author_id TEXT, '
            'author_name TEXT, timestamp INTEGER, rating INTEGER, comment TEXT, lang TEXT)')
        yield self._dbpool.runQuery(
            'CREATE INDEX IF NOT EXISTS reviews_app_id_idx ON reviews (app_id)')
        # create watchers table
        yield self._dbpool.runQuery(
            'CREATE TABLE IF NOT EXISTS watchers ' +
            '(id INTEGER PRIMARY KEY AUTOINCREMENT, app_id INTEGER, chat_id TEXT)')

    def get_apps(self):
        '''
        Get watched apps as deferred of list of tuples (id, app_name, app_desc).
        '''
        return self._dbpool.runQuery('SELECT * FROM apps')

    def get_app(self, app_name):
        '''
        Get watched app with given name as deferred of list of tuples (id, name).
        '''
        return self._dbpool.runQuery('SELECT * FROM apps WHERE name = ?', (app_name,))

    def add_app(self, app_name, app_desc):
        '''
        Add new app to list of watched apps.
        Returns deferred with added app id as its return value.
        '''
        return self._dbpool.runInteraction(self._txn_add_app, app_name, app_desc)

    def _txn_add_app(self, txn, app_name, app_desc):
        txn.execute('INSERT INTO apps (name, desc) VALUES (?, ?)', (app_name, app_desc,))
        return txn.lastrowid

    def delete_app(self, app_id):
        '''
        Delete app with given id from list of watched apps.
        '''
        return self._dbpool.runQuery('DELETE FROM apps WHERE id = ?', (app_id,))

    def get_reviews(self, app_id, author_id):
        '''
        Get reviews for an application by author id from database.
        '''
        return self._dbpool.runQuery('SELECT * FROM reviews WHERE app_id = ? AND author_id = ?',
                                     (app_id, author_id,))

    def add_review(self, app_id, author_id, author_name, timestamp, rating, comment, lang):
        '''
        Add new review of an application.
        '''
        return self._dbpool.runQuery(
            'INSERT INTO reviews (app_id, author_id, author_name, ' +
            'timestamp, rating, comment, lang) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (app_id, author_id, author_name, timestamp, rating, comment, lang,))

    def delete_reviews(self, app_id):
        '''
        Delete all reviews for an application with given id.
        '''
        return self._dbpool.runQuery('DELETE FROM reviews WHERE app_id = ?', (app_id,))

    def update_review(self, review_id, timestamp, rating, comment):
        '''
        Update an application review data.
        '''
        return self._dbpool.runQuery(
            'UPDATE reviews SET timestamp = ?, rating = ?, comment = ? WHERE id = ?',
            (timestamp, rating, comment, review_id,))

    def add_watcher(self, app_id, chat_id):
        '''
        Add an application watcher.
        '''
        return self._dbpool.runQuery('INSERT INTO watchers (app_id, chat_id) VALUES (?, ?)',
                                     (app_id, chat_id,))

    def delete_watcher(self, watcher_id):
        '''
        Delete application watcher with given id from list of watchers.
        '''
        return self._dbpool.runQuery('DELETE FROM watchers WHERE id = ?', (watcher_id,))

    def get_watcher(self, app_id, chat_id):
        '''
        Get watcher for an application.
        '''
        return self._dbpool.runQuery('SELECT * FROM watchers WHERE app_id = ? AND chat_id = ?',
                                     (app_id, chat_id,))

    def get_watchers(self, app_id):
        '''
        Get watchers for an application.
        '''
        return self._dbpool.runQuery('SELECT * FROM watchers WHERE app_id = ?', (app_id,))

    def get_watched_apps(self, chat_id):
        '''
        Get watched apps for chat as deferred of list of tuples (id, app_name, app_desc).
        '''
        return self._dbpool.runQuery(
            'SELECT app.id, app.name, app.desc FROM apps app ' +
            'INNER JOIN watchers w ON app.id = w.app_id WHERE w.chat_id = ?', (chat_id,))
