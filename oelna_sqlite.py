#!/usr/bin/env python3

import os
import sys
import sqlite3
import string
import random

from datetime import datetime
from rich.console import Console

console = Console()


class database():

	def __init__(self, db_file="database.db"):

		self.path = os.path.dirname(os.path.realpath(__file__))
		self.db_name = db_file

		self.connection = None
		self.db = None

		self.db_connect()

	def id_generator(self, size=6, chars=string.ascii_lowercase + string.digits):
		return ''.join(random.choice(chars) for _ in range(size))

	def db_connect(self):
		self.connection = sqlite3.connect(self.db_name)
		self.connection.row_factory = sqlite3.Row # object instead of tuple result (https://stackoverflow.com/a/20042292/3625228)
		self.db = self.connection.cursor()

		# todo: handle db upgrades/versions
		# https://stackoverflow.com/a/8030861/3625228

		sql = 'CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, firstname TEXT, lastname TEXT, voice TEXT DEFAULT "default", added INTEGER DEFAULT (cast(strftime(\'%s\', \'now\') as int)), version INTEGER DEFAULT 1, muted INTEGER DEFAULT 0)'
		self.db.execute(sql)

		# check sb version
		user_version = 1
		user_version_query = self.db_query("PRAGMA user_version")
		if len(user_version_query) > 0:
			if user_version_query[0] is not None:
				user_version = dict(user_version_query[0]).get("user_version")

		# upgrade to db v1
		if str(user_version) == "0":
			sql_update = (
				"ALTER TABLE users ADD COLUMN username_tts TEXT;"
				"PRAGMA user_version = 1;"
			)

			try:
				self.db.executescript(sql_update)
			except sqlite3.Error as er:
				print("Could not update db to user_version 1!")
			else:
				print("Updated db to user_version 1")

		print("connected to database. version %s" % user_version)

	def db_query(self, sql):
		try:
			self.db.execute(sql)
			return self.db.fetchall()
		except:
			return None

	# a very basic and insecure way to add data into sqlite tables
	def db_insert(self, table, columns=[], values=[]):
		cols = ', '.join(columns)
		cols_amount = len(columns)
		vals = ', '.join(['?']*cols_amount)
		
		try:
			sql = 'INSERT INTO %s (%s) VALUES(%s)' % (table, cols, vals)
			for row in values:
				if len(row) != cols_amount:
					# skip this row
					continue

				self.db.execute(sql, row)
				
			self.connection.commit()
			
		except sqlite3.OperationalError as e:
			print('SQL error')
			print(str(e))
		except sqlite3.IntegrityError as e:
			if str(e).find('UNIQUE constraint failed') != -1:
				print('unique constraint failed!')
			else:
				print('unknown error: ' + str(e))

		if self.db.rowcount < len(values):
			print('inserted only %s/%s rows' % (self.db.rowcount, len(values)))

		return self.db.rowcount

	def db_select(self, table, columns=[], params={}):
		
		data = []

		if type(columns) is str:
			columns = [columns]
		
		cols = ', '.join(columns)

		sql = 'SELECT %s FROM %s' % (cols, table)

		if 'where' in params and params['where'] is not None:
			if len(params['where']) > 0:
				sql += ' WHERE %s' % params['where']

		if 'group' in params and params['group'] is not None:
			if len(params['group']) > 0:
				sql += ' GROUP BY %s' % params['group']

		if 'order' in params and params['order'] is not None:
			if len(params['order']) > 0:
				sql += ' ORDER BY %s' % params['order']

		if 'limit' in params and params['limit'] is not None:
			if params['limit'] > -1:
				sql += ' LIMIT %s' % params['limit']

		if 'offset' in params and params['offset'] is not None:
			if params['offset'] > -1:
				sql += ' OFFSET %s' % params['offset']

		try:
			# print(sql)
			self.db.execute(sql)

			rows = self.db.fetchall()

			for row in rows:
				if row is not None:
					data.append(dict(row))

		except:
			print('Unexpected error')
			print(sys.exc_info())
			raise

		return data

	def db_update(self, table, columns=[], values=[], params={}):
		
		cols = '=?, '.join(columns)
		cols += '=?'

		sql = 'UPDATE %s SET %s' % (table, cols)

		if 'where' in params and params['where'] is not None:
			if len(params['where']) > 0:
				sql += ' WHERE %s' % params['where']

		if 'order' in params and params['order'] is not None:
			if len(params['order']) > 0:
				sql += ' ORDER BY %s' % params['order']

		if 'limit' in params and params['limit'] is not None:
			if params['limit'] > -1:
				sql += ' LIMIT %s' % params['limit']

		if 'offset' in params and params['offset'] is not None:
			if params['offset'] > -1:
				sql += ' OFFSET %s' % params['offset']

		try:
			for row in values:
				self.db.execute(sql, row)
				
			self.connection.commit()
			
		except sqlite3.OperationalError as e:
			print('SQL error')
			print(str(e))
		except sqlite3.IntegrityError as e:
			print('unknown error: ' + str(e))

		if self.db.rowcount < len(values):
			print('updated only %s/%s rows' % (self.db.rowcount, len(values)))
		
		return self.db.rowcount

	def db_delete(self, table, params={}):
		
		sql = 'DELETE FROM %s' % table

		if 'where' in params and params['where'] is not None:
			if len(params['where']) > 0:
				sql += ' WHERE %s' % params['where']

		if 'order' in params and params['order'] is not None:
			if len(params['order']) > 0:
				sql += ' ORDER BY %s' % params['order']

		if 'limit' in params and params['limit'] is not None:
			if params['limit'] > -1:
				sql += ' LIMIT %s' % params['limit']

		if 'offset' in params and params['offset'] is not None:
			if params['offset'] > -1:
				sql += ' OFFSET %s' % params['offset']

		try:
			self.db.execute(sql)
			self.connection.commit()
			
		except sqlite3.OperationalError as e:
			print('SQL error')
			print(str(e))
		except sqlite3.IntegrityError as e:
			print('unknown error: ' + str(e))

		return self.db.rowcount

if __name__ == '__main__':
	db = database()
