#!/usr/bin/env python3

import sys
import os

# TL;DR just use loop.run_in_executor to do blocking work

# sys.path.append(os.path.abspath("/home/el/foo4/stuff"))

# print(sys.version)
import importlib
import asyncio
import websockets
import ssl
# import socket
import requests
import string
import uuid
import json
import time
import random
import re
import math

from datetime import datetime
from AppKit import NSSound # play audio
from rich.console import Console

# from emoji import demojize

console = Console()

# from oelna_sqlite import database
db = importlib.import_module('oelna_sqlite')



class TwitchBot():

	def __init__(self):

		self.config = {}

		self.path = os.path.dirname(os.path.realpath(__file__))
		# self.db_name = os.path.splitext(__file__)[0] + '.db'
		self.db_name = "%s/%s" % (self.path, "v9-database.db")
		self.config_file = "%s/%s" % (self.path, "v9-config.json")
		self.messages_file = "%s/%s" % (self.path, "v9-messages.json")
		self.sounds_file = "%s/%s" % (self.path, "v9-sounds.json")
		self.chat_log_dir = "/Users/oelna/Desktop/twitch_logs"

		# load config data
		try:
			self.config = self.load_json(self.config_file)
		except:
			print("Error loading config file!")
			pass

		self.connections = {
			"irc": {
				"conn": None,
				"connection_attempts": 0,
				"seconds_since_startup": 0,
				"simulate_reconnect": False
			},
			"pubsub": {
				"conn": None,
				"connection_attempts": 0,
				"seconds_since_startup": 0,
				"simulate_reconnect": False
			},
		}

		'''
		self.socket = None
		self.connection_attempts = 0
		self.seconds_since_startup = 0
		self.simulate_reconnect = False # set to True to simulate a connection problem
		'''

		self.db = db.database(self.db_name)

		self.logs_dir = "/Users/oelna/Desktop/twitch_logs"

		# periodic messages
		self.periodic_messages = []
		try:
			self.periodic_messages = self.load_json(self.messages_file)
		except:
			print("Error loading messages file!")
			pass

		self.previous_message = None
		self.available_voices = ['Anna', 'Markus', 'Yannick', 'Petra']
		self.muted = False

		# load sounds
		self.sounds = {}
		try:
			self.sounds = self.load_json(self.sounds_file)
		except:
			print("Error loading sounds file!")
			pass

		# get some fresh access tokens
		self.refresh_token("bot")
		self.refresh_token("channel")

		# todo: reevaluate this hack!
		loop = asyncio.get_event_loop() 

		# self.channel_info = await self.api_get_user_data(self.config["channel"]["name"], "login")
		self.channel_info = loop.run_until_complete(self.api_get_user_data(self.config["channel"]["name"], "login"))

		# connect via asyncio later
		# self.connect()

	def truncate(self, input, n, filler="..."):
		# print("truncating to %s" % n)
		if len(input) <= n:
			return input

		maxlength = n - len(filler)

		if n <= len(filler):
			return input[:n]

		return (input[:maxlength] + filler) if len(input) > n else input

	def middle_truncate(self, input, n, filler="..."):
		# print("middle truncating to %s" % n)

		if len(input) <= n:
			return input

		max_length = n - len(filler)

		if n <= len(filler):
			return input[:n]

		if n <= max_length:
			return input

		if max_length < 0:
			# make the smallest possible string
			return "%s%s%s" % (input[0], filler, input[-1])

		start = math.ceil(max_length / 2)
		trunc = math.floor(max_length / 2)

		front = input[:start]
		back = input[-trunc:]
		
		return "%s%s%s" % (front, filler, back)

	def load_json(self, filename):
		with open(filename) as json_file:
			json_object = json.load(json_file)
			json_file.close()
		return json_object

	def save_json(self, filename, obj):
		with open(filename, "w", encoding="utf-8") as file:
			json.dump(obj, file, ensure_ascii=False, sort_keys=True, indent="\t")
		# print("Saved json data to file %s" % filename)

	def refresh_token(self, account):
		# todo: error handling

		url = "https://id.twitch.tv/oauth2/token"

		credentials = {
			"grant_type": "refresh_token",
			"refresh_token": self.config[account]["refresh_token"],
			"client_id": self.config[account]["client_id"],
			"client_secret": self.config[account]["client_secret"]
		}

		r = requests.post(url, data=credentials)

		if r.status_code == 200:
			response = json.loads(r.text)
			
			if account == "bot":
				self.config["bot"]["access_token"] = response["access_token"]
			else:
				self.config["channel"]["access_token"] = response["access_token"]

			self.config[account]["refresh_token"] = response["refresh_token"]
			self.config[account]["token_type"] = response["token_type"]

			self.config[account]["updated"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

			print("updated %s tokens" % account)
			# todo: save scope here as well?

			self.save_json(self.config_file, self.config)
		else:
			print("Could not get new tokens. Bad Request!")
			return False

		return True

	def generate_nonce(self):
		nonce = uuid.uuid1()
		oauth_nonce = nonce.hex
		return oauth_nonce

	async def connect_pubsub(self):

		# dangerous! via https://stackoverflow.com/a/57116834/3625228
		ssl_context = ssl.SSLContext()
		ssl_context.check_hostname = False
		ssl_context.verify_mode = ssl.CERT_NONE

		self.connections["pubsub"]["conn"] = await websockets.connect(self.config["server"]["pubsub"]["url"], ssl=ssl_context)
		if self.connections["pubsub"]["conn"].open:
			print('Connection to PubSub established.')
			
			# Send greeting
			message = {"type": "LISTEN", "nonce": str(self.generate_nonce()), "data":{"topics": self.config["server"]["pubsub"]["topics"], "auth_token": self.config["channel"]["access_token"]}}

			json_message = json.dumps(message)
			await self.send(self.connections["pubsub"]["conn"], json_message)
			
			return self.connections["pubsub"]["conn"]

	async def connect_irc(self):

		# dangerous! via https://stackoverflow.com/a/57116834/3625228
		ssl_context = ssl.SSLContext()
		ssl_context.check_hostname = False
		ssl_context.verify_mode = ssl.CERT_NONE

		self.connections["irc"]["conn"] = await websockets.connect(self.config["server"]["irc"]["url"], ssl=ssl_context)
		if self.connections["irc"]["conn"]:
			print('Connection to IRC established.')
			
			# Send greeting
			await self.send(self.connections["irc"]["conn"], 'PASS oauth:%s' % self.config["bot"]["access_token"])
			await self.send(self.connections["irc"]["conn"], 'NICK %s' % self.config["bot"]["name"])

			await self.send(self.connections["irc"]["conn"], 'CAP REQ :twitch.tv/membership')
			await self.send(self.connections["irc"]["conn"], 'CAP REQ :twitch.tv/tags')
			await self.send(self.connections["irc"]["conn"], 'CAP REQ :twitch.tv/commands')

			await self.send(self.connections["irc"]["conn"], 'JOIN #%s' % self.config["channel"]["name"])
			
			return self.connections["irc"]["conn"]

	def connect(self):

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# get new access token
		self.refresh_token("bot")
		self.refresh_token("channel")

		# self.api_get_user_data(self.config["channel"]["name"])

		try:
			self.socket.connect((self.config["server"]["url"], self.config["server"]["port"])) # Here we connect to the server using the port 6667
			self.socket.settimeout(1)
			# todo: make this non-blocking?
			# https://medium.com/vaidikkapoor/understanding-non-blocking-i-o-with-python-part-1-ec31a2e2db9b
		except socket.error:
			self.socket.close()
			print("Error while connecting to socket")
			sys.exit(0)
		
		self.send('PASS oauth:%s' % self.config["bot"]["access_token"])
		self.send('NICK %s' % self.config["bot"]["name"])
		self.send('USER %s 0 * %s' % (self.config["bot"]["name"], self.config["bot"]["name"]))
		
		self.send('CAP REQ :twitch.tv/membership')
		self.send('CAP REQ :twitch.tv/tags')
		self.send('CAP REQ :twitch.tv/commands')
		
		self.send('JOIN #%s' % self.config["channel"]["name"])

		self.loop()

	def reconnect(self):
		self.socket.close()
		self.connection_attempts += 1

		timeout = pow(2, self.connection_attempts)
		print("trying to reconnect. waiting for %s seconds." % timeout)

		time.sleep(timeout)

		# self.simulate_reconnect = False
		self.connect()

	async def periodic(self):
		while True:
			# internal clock
			self.connections["irc"]["seconds_since_startup"] += 1

			# periodic messages
			for periodic_msg in self.periodic_messages:
				if self.connections["irc"]["seconds_since_startup"] % periodic_msg.get('interval', 0) == 0:
					await self.message(periodic_msg.get('message'))

			await asyncio.sleep(1)

	async def heartbeat_pubsub(self, connection):
		while True:
			try:
				data_set = { "type": "PING" }
				json_request = json.dumps(data_set)

				await self.send(connection, json_request)
				await asyncio.sleep(60)
				self.connections["pubsub"]["seconds_since_startup"] += 60
			except websockets.exceptions.ConnectionClosed:
				print('Heartbeat with pubsub server closed')
				break

	async def on_message_pubsub(self, connection):
		while True:
			try:
				message = await connection.recv()
				msg = json.loads(message)

				if msg['type'] == 'RESPONSE':
					if msg['error'] == '':
						console.print('PubSub connection successful.')
					else:
						print('An error occurred during PubSub login:')
						console.print(msg)
						# sys.exit(0)

				elif msg['type'] == 'PONG':
					# don't show anything here
					pass

				elif msg['type'] == 'MESSAGE':
					# got a message
					msg_content = json.loads(msg['data']['message'])

					if msg['data']['topic'].startswith('channel-subscribe-events-v1.'):
						# todo: handle sub event
						'''
						{
							"type": "MESSAGE",
							"data": {
								"topic": "channel-subscribe-events-v1.59039718",
								"message": "{\"benefit_end_month\":0,\"user_name\":\"streamblox_\",\"display_name\":\"streamblox_\",\"channel_name\":\"oelna81\",\"user_id\":\"116584342\",\"channel_id\":\"59039718\",\"recipient_id\":\"501392856\",\"recipient_user_name\":\"selimhex\",\"recipient_display_name\":\"selimhex\",\"time\":\"2021-12-10T10:25:03.945891885Z\",\"sub_message\":{\"message\":\"\",\"emotes\":null},\"sub_plan\":\"1000\",\"sub_plan_name\":\"Stackoverflow Expert\",\"months\":2,\"context\":\"subgift\",\"is_gift\":true,\"multi_month_duration\":1}"
							}
						}
						'''
						console.print(msg)
						pass

					if msg['data']['topic'].startswith('channel-bits-events-v2.'):
						# todo: handle bits event
						console.print(msg)
						pass
					
					if msg['data']['topic'].startswith('channel-points-channel-v1'):
						if msg_content['type'] == 'reward-redeemed':
							
							user = msg_content['data']['redemption']['user']['login']
							reward = msg_content['data']['redemption']['reward']['title']
							reward_id = msg_content['data']['redemption']['reward']['id']
							isodate = msg_content['data']['timestamp'] # RFC 3339 date

							user_input = ''
							if msg_content['data']['redemption']['reward']['is_user_input_required'] == True:
								user_input = ' (%s)' % msg_content['data']['redemption']['user_input']

							ts = datetime.fromisoformat(isodate[0:19])
							time = ts.strftime('%H:%M:%S')

							is_sub = self.api_get_sub_status(self.channel_info["data"][0]["id"], msg_content['data']['redemption']['user']['id'])
							
							message_status = ""
							if is_sub:
								message_status = "\[sub] "

							console.print('[orange1][%s] %s%s redeemed "%s"%s[/orange1]' % (time, message_status, user, reward, user_input))
							# print(reward_id)
							self.playsound('cat')
							# time.sleep(1)
							await asyncio.sleep(1)
							say_string = 'say -v %s "%s hat %s eingelöst!"' % (self.available_voices[0], user, reward)
							os.system(say_string)

				else:
					print('Something weird: %s' % msg)

			except websockets.exceptions.ConnectionClosed:
				print('Connection to pubsub server was closed.')
				# todo: reconnect?
				break

	async def on_message_irc(self, connection):
		while True:
			try:
				data = await connection.recv()
				messages = data.split("\r\n")

				for raw_message in messages:
					if len(raw_message) > 0:
						message = self.parse_message(raw_message)
						if message is not None:
							await self.handle_message(message)
							self.previous_message = message # preserve in buffer

			except websockets.exceptions.ConnectionClosed:
				print('Connection to irc server was closed.')
				# todo: reconnect?
				break

	def loop(self):
		while True:

			if self.simulate_reconnect is True:
				self.reconnect()

			# internal clock
			self.seconds_since_startup += 1

			# periodic messages
			for periodic_msg in self.periodic_messages:
				if self.seconds_since_startup % periodic_msg.get('interval', 0) == 0:
					self.message(periodic_msg.get('message'))

			try:
				data = self.socket.recv(2048).decode("UTF-8")
			except ConnectionResetError:
				print('\nConnection reset. Reconnecting …')
				self.reconnect()
				break
			except (KeyboardInterrupt, SystemExit):
				print('\nExiting ...') # got Ctrl-C
				self.send("QUIT")
				self.socket.close()
				sys.exit(0)
				break
			except socket.timeout:
				# do nothing, just keep waiting
				continue
			else:
				if len(data) == 0:
					print('Orderly shutdown on server end. Reconnecting …')
					self.reconnect()

			messages = data.split("\r\n")

			for raw_message in messages:
				if len(raw_message) > 0:
					message = self.parse_message(raw_message)
					if message is not None:
						self.handle_message(message)
						self.previous_message = message # preserve in buffer

	async def handle_privmsg(self, message):

		msg_status = []
		msg_status_str = ''

		if message['mod']:
			msg_status.append('mod')
			
		if message['sub']:
			msg_status.append('sub')

		if len(msg_status) > 0:
			msg_status_str = ','.join(msg_status)
			msg_status_str = "[bright_green]\[%s][/bright_green] " % msg_status_str

		# set a beautiful display name
		try:
			display_name = message["tags"]["display-name"]
		except:
			display_name = message["nick"] if message["nick"] is not None else message["prefix"]
		
		if "bits" in message.get("tags"):
			self.playsound('achja')
			await self.message('@%s Danke!' % message['nick'])
			console.print("[%s] %s%s: [+%s Bits!] [orange1]%s[/orange1]" % (message['time'], msg_status_str, display_name, message['tags']['bits'], message['text']))
			# time.sleep(1)
			await asyncio.sleep(1)
			# say_string = 'say -v %s "%s%s"' % (self.available_voices[0], "Danke für die Bits, ", message['nick'])
			# os.system(say_string)
			# time.sleep(2)
		else:
			console.print("[%s] %s%s: %s" % (message['time'], msg_status_str, display_name, message['text']))

		# handle commands starting with !
		if message["text"].startswith("!"):
			await self.handle_command(message)

		# get db data for user
		try:
			user_data = self.db_get_user(message['nick'].lower())
		except:
			user_data = None

		if user_data is None:
			# create new user entry
			check = self.db_add_user(message['nick'].lower())
			if not check:
				console.print('[red]could not create new user "%s"![/red]' % message['nick'].lower())
			else:
				user_data = self.db_get_user(message['nick'].lower())

		# speak message text
		if self.muted == False:
			if 'muted' in user_data and user_data['muted'] != 1:
				# silence commands and mentions
				if not message['text'].startswith("!") and not message['text'].startswith("@"):
					user = '';
					if self.previous_message["nick"] != user_data["username"]:
						rnd_str = random.choice(['sagt', 'meint', 'behauptet', 'merkt an', 'hat gesagt'])
						user = '%s %s, ' % (message['nick'], rnd_str)

					clean_text = message['text'].replace('"','\"')
					clean_text = clean_text.replace('`','\"')
					clean_text = re.sub(r'(https|http|ftp|ssh):\/\/\S+', 'URL', clean_text) # replace links
					clean_text = clean_text.replace('-',' ')
					clean_text = clean_text.replace('<','(')
					clean_text = clean_text.replace('>',')')

					# handle custom voices
					user_voice = self.available_voices[0]
					if user_data['voice'] != 'default':
						user_voice = user_data['voice']

					say_string = 'say -v %s "%s%s"' % (user_voice, user.replace('"','\"'), clean_text)

					os.system(say_string)

	async def handle_command(self, message):
		command = message["text"][1:].strip().split(' ')

		# look for modules in the 'commands' dir first
		# and import/run, if available
		status = None
		if not command[0].startswith("_"): # skip commands that start with _
			try:
				module = importlib.import_module('commands.%s' % command[0])
				status = await module.init(self, message, command)
			except:
				# no dynamic module for this command was found
				pass
			else:
				if status is not None:
					# this command has been handled. return early
					return

		# mute and unmute users
		if command[0] == "mute":
			if message['mod'] == True or message['broadcaster'] == True:
				if len(command) > 1:
					check = self.db_update_user(command[1], 'muted', 1)
					if check:
						await self.message('perma-muted user %s' % command[1])
				else:
					# mute everything
					self.muted = True
					await self.message('temporarily muted all of chat')

		if command[0] == "unmute":
			if message['mod'] == True or message['broadcaster'] == True:
				if len(command) > 1:
					check = self.db_update_user(command[1], 'muted', 0)
					if check:
						await self.message('gave user %s a voice again!' % command[1])
				else:
					# mute everything
					self.muted = False
					await self.message('unmuted all of chat, finally!')

		# check for sounds
		if command[0] in self.sounds:
			if self.muted == False:
				self.playsound(command[0], message)

		# handle user settings
		if command[0] == "user":
			if len(command) > 1:
				if command[1] == 'voice':
					if len(command) > 2:
						new_voice = command[2].title()
						if new_voice in self.available_voices:
							# print('setting voice to "%s"' % new_voice)
							check = self.db_update_user(message['nick'], 'voice', new_voice)
							if check:
								await self.message('@%s set your voice to %s' % (message['nick'], new_voice))
						else:
							await self.message('@%s available voices are %s' % (message['nick'], ', '.join(self.available_voices)))
					else:
						await self.message('@%s you need to set a value for voice, such as %s' % (message['nick'], ', '.join(self.available_voices)))
				elif command[1] == 'tts' and len(command) > 2:
					check = self.db_update_user(message['nick'], 'username_tts', command[2].strip())
					if check:
						await self.message('@%s set your tts username to %s' % (message['nick'], command[2].strip()))
				elif command[1] == 'firstname' and len(command) > 2:
					check = self.db_update_user(message['nick'], 'firstname', command[2].strip())
					if check:
						await self.message('@%s set your first name to %s' % (message['nick'], command[2].strip()))
				elif command[1] == 'lastname' and len(command) > 2:
					check = self.db_update_user(message['nick'], 'lastname', command[2].strip())
					if check:
						await self.message('@%s set your last name to %s' % (message['nick'], command[2].strip()))
				elif command[1] == 'info' and len(command) > 2:
					info_string = "info for user %s" % command[2].strip().lower()
					
					try:
						db_data = self.db_get_user(command[2].strip().lower())

						fn = db_data.get('firstname')
						ln = db_data.get('lastname')
						if (fn is not None) or (ln is not None):
							info_string = "%s, identifies as %s %s" % (info_string, fn, ln)

						muted = db_data.get('muted', 0) == 1
						info_string = "%s, %s" % (info_string, "muted" if muted else "not muted")
					except:
						info_string = "%s, no channel database info available" % info_string
						pass

					try:
						api_data = await self.api_get_user_data(command[2].strip().lower())
						api_user = api_data.get("data", [])
						if len(api_user) > 0:
							user_id = api_user[0].get("id")
							info_string = "%s, id:%s" % (info_string, user_id)

							user_type = api_user[0].get("broadcaster_type", "")
							user_type = user_type if user_type != "" else "normal"
							info_string = "%s, type: %s" % (info_string, user_type)

							info_string = "%s, view count: %s" % (info_string, api_user[0].get("view_count", "unknown"))

							user_create_date = api_user[0].get("created_at") # 2014-03-16T13:19:36Z
							user_create_date_object = datetime.strptime(user_create_date, '%Y-%m-%dT%H:%M:%SZ')
							user_create_date_string = user_create_date_object.strftime('%Y-%m-%d')
							info_string = "%s, created on %s" % (info_string, user_create_date_string)
						else:
							info_string = "%s, no API info available. user does not exist." % info_string
					except:
						pass

					await self.message(info_string)
				else:
					await self.message('@%s use `!user command value` to set a value' % message['nick'])
			else:
				await self.message('@%s available commands are firstname, lastname, voice, info' % message['nick'])

	async def handle_usernotice(self, message):
		if message['tags']['msg-id']:
			if message['tags']['msg-id'] == 'sub':

				print_string = "[%s] %s just subscribed (1)!" % (message['time'], message['tags']['display-name'])
				say_string = 'say -v %s "%s %s"' % (self.available_voices[0], message['tags']['display-name'].replace('"','\"'), 'hat abonniert')

				# handle custom message by the sub
				if message["text"] is not None:
					print_string = "%s Message: %s" % (print_string, message["text"])
					say_string = "%s und sagt: %s" % (say_string, message["text"])

				console.print("[orange1]%s[/orange1]" % print_string)
				await self.message('@%s Danke!!' % message['tags']['display-name'])
				self.playsound('achja')
				# time.sleep(1)
				await asyncio.sleep(1)
				os.system(say_string)

			elif message['tags']['msg-id'] == 'resub':
				months = message["tags"]["msg-param-cumulative-months"] if "msg-param-cumulative-months" in message["tags"] else "unknown"
				print_string = "[%s] %s has resubscribed (%s)!" % (message['time'], message['tags']['display-name'], months)
				say_string = 'say -v %s "%s %s"' % (self.available_voices[0], message['tags']['display-name'].replace('"','\"'), 'hat wieder abonniert')

				# handle custom message by the sub
				if message["text"] is not None:
					print_string = "%s Message: %s" % (print_string, message["text"])
					say_string = "%s und sagt: %s" % (say_string, message["text"])

				console.print("[orange1]%s[/orange1]" % print_string)
				await self.message('@%s Danke!!' % message['tags']['display-name'])
				self.playsound('achja')
				#time.sleep(1)
				await asyncio.sleep(1)
				os.system(say_string)

			elif message['tags']['msg-id'] == 'subgift':
				print_string = "[%s] %s has gifted a sub to %s!" % (message['time'], message['tags']['display-name'], message['tags']['msg-param-recipient-display-name'])
				say_string = 'say -v %s "%s hat %s ein Abo geschenkt!"' % (self.available_voices[0], message['tags']['display-name'].replace('"','\"'), message['tags']['msg-param-recipient-display-name'].replace('"','\"'))

				console.print("[orange1]%s[/orange1]" % print_string)
				await self.message('@%s Danke!!' % message['tags']['display-name'])
				self.playsound('achja')
				# time.sleep(1)
				await asyncio.sleep(1)
				os.system(say_string)

			elif message['tags']['msg-id'] == 'raid':
				print_string = "[%s] %s is raiding the channel with %s viewers!" % (message['time'], message['tags']['display-name'], message['tags']['msg-param-viewerCount'])
				say_string = 'say -v %s "%s raided dich mit %s Zuschauenden!"' % (self.available_voices[0], message['tags']['display-name'].replace('"','\"'), message['tags']['msg-param-viewerCount'])

				console.print("[orange1]%s[/orange1]" % print_string)
				await self.message('@%s Danke!!' % message['tags']['display-name'])
				self.playsound('record')
				# time.sleep(1)
				await asyncio.sleep(1)
				os.system(say_string)

	async def handle_message(self, message):
		if message["command"] is not None:
			if message["command"] == "PRIVMSG":
				await self.handle_privmsg(message)
			elif message["command"] == "USERNOTICE":
				# todo: handle subs, etc
				# print("usernotice: %s" % message["raw"])
				await self.handle_usernotice(message)
			elif message["command"] == "ROOMSTATE":
				# don't output roomstate messages for now
				pass
			elif message["command"] == "USERSTATE":
				# don't output roomstate messages for now
				pass
			elif message["command"] == "JOIN":
				ts = datetime.now().strftime('%H:%M:%S')
				console.print("[deep_sky_blue1][%s] %s joined![/deep_sky_blue1]" % (ts, message["nick"]))
			elif message["command"] == "PART":
				ts = datetime.now().strftime('%H:%M:%S')
				console.print("[dark_red][%s] %s left![/dark_red]" % (ts, message["nick"]))
			elif message["command"] == "PING":
				# handle ping/pong silently, don't log
				pong = message["raw"].replace("PING", "PONG")
				await self.send(self.connections["irc"]["conn"], pong)
				return
			elif message["command"] == "366":
				# the connection seems to be working, reset attempts
				self.connection_attempts = 0
				console.print("IRC login successful.")
			else:
				print(message["raw"])

			self.log(message)

	def log(self, message):
		filename = "%s/%s.txt" % (self.chat_log_dir, datetime.today().strftime("%Y-%m-%d"))
		with open(filename, 'a') as log_file:
			log_file.write("[%s] " % message["time"] + message["raw"] + "\n")

	async def send(self, connection, str):
		
		await connection.send(str)
		
		if connection._host == self.config["server"]["irc"]["url"][6:]:
			# is IRC message
			if str.startswith('PASS '):
				console.print('[<] ' + self.truncate(str, 24, "…"), style="dim green")
				return
			if str.startswith('PONG'):
				return
			if str.find("PRIVMSG #") != -1:
				# this is a regular chat message
				now = datetime.utcnow().strftime('%H:%M:%S')
				text = str.split(':', 1)[1]
				console.print("[%s] %s" % (now, text), style="orange1")
				return
			else:
				console.print('[<] ' + str, style="green")
		else:
			# is PubSub message
			# usually do nothing
			# console.print('[<] ' + str, style="green")
			pass

	async def message(self, str):
		await self.send(self.connections["irc"]["conn"], 'PRIVMSG #%s :%s' % (self.config["channel"]["name"], str))

	def parse_message(self, data):
		# from https://github.com/BarryCarlyon/irc-message/blob/master/index.js
		# other reference https://github.com/oftc/qwebirc-websocket/blob/master/js/irc/ircparser.js

		if len(data) < 1:
			return None

		message = {
			"raw": data,
			"tags": {},
			"prefix": None,
			"command": None,
			"params": [],

			"nick": None,
			"channel": None,
			"text": None,
			"timestamp": None,
			"date": None,
			"time": None,

			"broadcaster": False,
			"mod": False,
			"sub": False
		}

		position = 0
		nextspace = 0

		if ord(data[0]) == 64:
			nextspace = data.find(' ')

			if nextspace == -1:
				return None

			raw_tags = data[1:nextspace].split(";")

			for i in range(0, len(raw_tags)):
				tag = raw_tags[i]

				split = tag.split('=')
				if len(split) < 3: # ignore malformed tags?
					key, val = split
					message["tags"][key.strip()] = val.strip() if len(val) > 0 else True

			position = nextspace + 1

		# Skip any trailing whitespace.
		while ord(data[position]) == 32:
			position += 1

		if ord(data[position]) == 58:
			nextspace = data.find(' ', position)

			if nextspace == -1:
				return None

			message["prefix"] = data[position+1:nextspace]
			position = nextspace + 1

			while ord(data[position]) == 32:
				position += 1

		nextspace = data.find(' ', position)

		if nextspace == -1:
			if len(data) > position:
				message["command"] = data[position:]
				return message

			return None

		message["command"] = data[position:nextspace]

		position = nextspace + 1

		while ord(data[position]) == 32:
			position += 1

		while position < len(data):
			nextspace = data.find(' ', position)

			if ord(data[position]) == 58:
				message["params"].append(data[position+1:])
				break

			if nextspace != -1:
				message["params"].append(data[position:nextspace])
				position = nextspace + 1

				while ord(data[position]) == 32:
					position += 1

				continue

			if nextspace == -1:
				message["params"].append(data[position:])
				break

		# convenience fields
		if message["params"][0] is not None and message["params"][0][0] == "#":
			message["channel"] = message["params"][0][1:]

		if 1 < len(message["params"]) and message["params"][1] is not None:
			message["text"] = message["params"][1]

		if message["prefix"] is not None and len(message["prefix"]) > 0:
			if message["prefix"].find("!") != -1 and message["prefix"].find("@") != -1:
				nick, rest = message["prefix"].split("!")
				if len(nick) > 0:
					message["nick"] = nick.lower()

		# channel owner
		if message["nick"] == self.config["channel"]["name"]:
			message["broadcaster"] = True

		# mod status
		try:
			message["mod"] = message["tags"]["mod"] == "1"
		except:
			pass

		# sub status
		try:
			message["sub"] = message["tags"]["subscriber"] == "1"
		except:
			pass

		# build timestamps
		ts = 0
		if "tmi-sent-ts" in message["tags"]:
			ts = int(message["tags"]["tmi-sent-ts"]) / 1000
		message["timestamp"] = int(ts)
		message["date"] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
		message["time"] = datetime.fromtimestamp(ts).strftime('%H:%M:%S')

		return message

	def db_add_user(self, username):

		# select a random voice for the new user
		new_voice = random.choice(self.available_voices)

		result = self.db.db_insert('users', ['username', 'voice'], [
			[username, new_voice]
		])

		if result == 1:
			print('created user "%s"' % username)
		return result

	def db_get_user(self, username):

		data = self.db.db_select('users', '*', {
			'where': 'username = "%s"' % username,
			'limit': 1
		})

		if data is None or len(data) < 1:
			# user does not exist, no record found
			return None

		return data[0]

	def db_update_user(self, username, column, value):

		result = self.db.db_update('users', [column], [
			[value]
		], {
			'where': 'username = "%s"' % username
		})

		return result

	def playsound(self, soundname, message=None):

		now = datetime.utcnow().timestamp()

		if self.sounds[soundname].get('disabled') != True:
			if self.sounds[soundname].get('sub_only') == True and message is not None:
				try:
					if message['sub'] != True:
						return
				except:
					pass

			if now > self.sounds[soundname].get('last_played', 0) + self.sounds[soundname].get('timeout', 0):
				self.sounds[soundname]['last_played'] = now

				self.sounds[soundname]['ref'] = NSSound.alloc()
				self.sounds[soundname]['ref'].initWithContentsOfFile_byReference_(self.sounds[soundname]['file'], True)
				self.sounds[soundname]['ref'].play()
				
				# time.sleep(self.sounds[soundname]['ref'].duration())
		else:
			print("sound is disabled!")

	async def api_set_stream_title(self, title, from_message=None):

		try:
			channel_data = await self.api_get_user_data(self.config["channel"]["name"])
			channel_items = channel_data.get("data", [])
			if len(channel_items) > 0:
				channel_id = channel_items[0].get("id")
			else:
				return None
		except:
			console.print("[red]Could not get channel ID! Aborting![/red]")
			return None

		if from_message is not None:
			await self.message("%s set the title to %s" % (from_message["nick"], title))
		else:
			await self.message("Setting title to %s" % title)

		url = "https://api.twitch.tv/helix/channels"

		credentials = {
			"Authorization": "Bearer %s" % self.config["channel"]["access_token"],
			"Client-Id": self.config["channel"]["client_id"],
			"Content-Type": "application/json"
		}

		request = requests.patch(url, data=json.dumps({ "title" : title }), params={ "broadcaster_id" : channel_id }, headers=credentials)

		if request.status_code == 200 or request.status_code == 204:
			# No content response!
			return True
		else:
			console.print("[red]No API response for %s[/red]" % url)
			console.print(request)
			return None

	async def api_get_channel_data(self, identifier, type="login"):

		url = "https://api.twitch.tv/helix/streams"

		credentials = {
			"Authorization": "Bearer %s" % self.config["channel"]["access_token"],
			"Client-Id": self.config["channel"]["client_id"]
		}

		parameters = {}
		if type.lower() == "id":
			parameters["user_id"] = int(identifier)
		else:
			parameters["user_login"] = str(identifier).lstrip('#').lstrip('@')
		
		try:
			request = requests.get(url, headers=credentials, params=parameters)
		except:
			print('API error')

		if request.status_code == 200:
			response = json.loads(request.text)
			return response
		else:
			return None

	async def api_get_user_data(self, identifier, type="login"):

		url = "https://api.twitch.tv/helix/users"

		credentials = {
			"Authorization": "Bearer %s" % self.config["channel"]["access_token"],
			"Client-Id": self.config["channel"]["client_id"]
		}

		parameters = {}
		if type.lower() == "id":
			parameters["id"] = int(identifier)
		else:
			parameters["login"] = str(identifier).lstrip('#').lstrip('@')

		request = requests.get(url, headers=credentials, params=parameters)

		if request.status_code == 200:
			response = json.loads(request.text)
			return response
		else:
			return None

	def api_get_sub_status(self, broadcaster_id, user_id):

		url = "https://api.twitch.tv/helix/subscriptions"

		credentials = {
			"Authorization": "Bearer %s" % self.config["channel"]["access_token"],
			"Client-Id": self.config["channel"]["client_id"]
		}

		parameters = {}
		parameters["broadcaster_id"] = int(broadcaster_id)
		parameters["user_id"] = int(user_id)
		parameters["first"] = 1

		try:
			request = requests.get(url, headers=credentials, params=parameters)
		except:
			print('API error')

		if request.status_code == 200:
			response = json.loads(request.text)

			if "data" in response:
				if len(response["data"]) > 0:
					return True
			return False
		else:
			return False

if __name__ == '__main__':
	
	# Creating client object
	client = TwitchBot()
	loop = asyncio.get_event_loop()

	# Start connection and get client connection protocol
	connection_irc = loop.run_until_complete(client.connect_irc())
	connection_pubsub = loop.run_until_complete(client.connect_pubsub())

	tasks = [
		asyncio.ensure_future(client.on_message_irc(connection_irc)),
		asyncio.ensure_future(client.periodic()),
		asyncio.ensure_future(client.on_message_pubsub(connection_pubsub)),
		asyncio.ensure_future(client.heartbeat_pubsub(connection_pubsub)),
	]

try:
	loop.run_until_complete(asyncio.wait(tasks))
except KeyboardInterrupt:
	print(" Goodbye!")
