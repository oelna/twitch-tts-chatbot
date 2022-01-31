#!/usr/bin/env python3

import os
import random
import time
import json

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return
	
	if len(command) < 3:
		result_string = "Syntax: !blackjack <username> [new, status, hit, stand, help]"
	elif message["nick"].lower() == command[1].lower():
		result_string = "You can't play yourself, dummy!"
	else:
		# let's play!
		blackjack = Blackjack(message["nick"], command[1], command[2])
		result_string = blackjack.get_status()
	
	# todo: players that stand should not be prompted again to play, but be skipped over
	
	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass

class Blackjack():
	def __init__(self, user1, user2, command):
		self.user1 = self.clean_name(user1)
		self.user2 = self.clean_name(user2)
		self.command = command
		self.status = []
		
		self.path = os.path.dirname(os.path.realpath(__file__))
		self.matches_path = "%s/blackjack-matches" % (self.path)
		self.winvalue = 21
		
		self.deck = [
			['c','A'],['c','2'],['c','3'],['c','4'],['c','5'],['c','6'],['c','7'],['c','8'],['c','9'],['c','10'],['c','B'],['c','D'],['c','K'],
			['s','A'],['s','2'],['s','3'],['s','4'],['s','5'],['s','6'],['s','7'],['s','8'],['s','9'],['s','10'],['s','B'],['s','D'],['s','K'],
			['h','A'],['h','2'],['h','3'],['h','4'],['h','5'],['h','6'],['h','7'],['h','8'],['h','9'],['h','10'],['h','B'],['h','D'],['h','K'],
			['d','A'],['d','2'],['d','3'],['d','4'],['d','5'],['d','6'],['d','7'],['d','8'],['d','9'],['d','10'],['d','B'],['d','D'],['d','K']
		]
		
		# fake
		self.deck_keys = list(range(0, len(self.deck)))

		self.run()
	
	def get_status(self):
		return " ".join(self.status)
	
	def add_status(self, str):
		self.status.append(str)
	
	def clean_name(self, str):
		clean_str = str.strip().lower()
		clean_str = clean_str.lstrip("@")
		
		return clean_str
	
	def draw(self):
		random_key = random.randint(0, len(self.deck_keys)-1)
		card_key = self.deck_keys[random_key]
		del(self.deck_keys[random_key])
		
		return card_key
	
	def card_name(self, index):
		suit = ""

		if self.deck[index][0] == "c":
			suit = "Clubs ♣"
		elif self.deck[index][0] == "s":
			suit = "Spades ♠"
		elif self.deck[index][0] == "s":
			suit = "Diamonds ♦"
		else:
			suit = "Hearts ♥"
		
		value = ""

		if self.deck[index][1] == "B":
			value = "Jack"
		elif self.deck[index][1] == "D":
			value = "Queen"
		elif self.deck[index][1] == "K":
			value = "King"
		elif self.deck[index][1] == "A":
			value = "Ace"
		else:
			value = self.deck[index][1]
		
		return "%s of %s" % (value, suit)
	
	def card_sum(self, arr):
		value = 0
		
		for index in arr:
			extra = ["B", "D", "K"]
			aces = 0
			
			if self.deck[index][1] in extra:
				value += 10
			elif self.deck[index][1] == "A":
				aces += 1
			else:
				value += int(self.deck[index][1])
			
			# todo: improve upon ace math
			if aces > 1:
				value += 1
			elif aces == 1:
				value += 1
			
		return value
	
	def run(self):
		if len(self.user1) > 0 and len(self.user2) > 0 and len(self.command) > 0:
			players = [
				self.user1,
				self.user2
			]
			players = sorted(players)
			
			filename = "-".join(players)
			filename = "%s.json" % filename.lower()
		else:
			self.add_status("Syntax: !blackjack <username> [new, status, hit, stand, help]")
			# do nothing?
			return
		
		if self.command.lower() == "new":
			player_cards = {
				self.user1: [],
				self.user2: []
			}
			
			match_data = {
				"nextPlayer": "selimhex",
				"matchStarted": int(time.time()),
				"matchActive": int(time.time()),
				"matchEnded": False,
				"stand": [],
				"players": player_cards
			}
		
			for i in range(0, len(players)):
				for player in players:
					card_index = self.draw()
					card_name = self.card_name(card_index)
					self.add_status("%s drew %s," % (player, card_name))
					match_data["players"][player].append(card_index)
					
			for player in players:
				self.add_status("%s has: %d." % (player, self.card_sum(match_data["players"][player])))
			
			match_data["nextPlayer"] = random.randint(0, len(players)-1)
			
			self.add_status("It's %s's turn!" % players[match_data["nextPlayer"]])
			
			with open("%s/%s" % (self.matches_path, filename), "w", encoding="utf-8") as file:
				json.dump(match_data, file, ensure_ascii=False, sort_keys=True, indent="\t")
		
		elif self.command.lower() == "status":
			try:
				with open("%s/%s" % (self.matches_path, filename)) as file_content:
					match_data = json.load(file_content)
			except:
				self.add_status("This match is not currently running. Start a new one?")
				return
			
			if match_data["matchEnded"] == True:
				self.add_status("This match has ended. Start a new one?")
				return
			
			sum_player1 = self.card_sum(match_data["players"][players[0]])
			sum_player2 = self.card_sum(match_data["players"][players[1]])
			
			self.add_status("%s has %d." % (players[0], sum_player1))
			self.add_status("%s has %d." % (players[1], sum_player2))
			
			self.add_status("It's %s's turn!" % players[match_data["nextPlayer"]])
			return
		
		elif self.command.lower() == "help":
			self.add_status("Syntax: !blackjack <username> [new, status, hit, stand, help]")
			return
		
		elif self.command.lower() == "stand":
			try:
				with open("%s/%s" % (self.matches_path, filename)) as file_content:
					match_data = json.load(file_content)
			except:
				self.add_status("This match is not currently running. Start a new one?")
				return
			
			if players[match_data["nextPlayer"]] == self.user1:
				if self.user1 not in match_data["stand"]:
					match_data["stand"].append(self.user1)
					
				if len(match_data["stand"]) == len(players):
					self.add_status("All stand.")
					
					match_data["matchEnded"] = True
						
					with open("%s/%s" % (self.matches_path, filename), "w", encoding="utf-8") as file:
						json.dump(match_data, file, ensure_ascii=False, sort_keys=True, indent="\t")
					
					sum_player1 = self.card_sum(match_data["players"][players[0]])
					sum_player2 = self.card_sum(match_data["players"][players[1]])
					
					self.add_status("%s has %d." % (players[0], sum_player1))
					self.add_status("%s has %d." % (players[1], sum_player2))
					
					if sum_player1 > sum_player2:
						self.add_status("%s won!" % players[0])
					elif sum_player1 < sum_player2:
						self.add_status("%s won!" % players[1])
					else:
						self.add_status("It's a tie!")
					
					try:
						os.remove("%s/%s" % (self.matches_path, filename))
					except:
						self.add_status("Could not delete match data file!")
						return
					return
				else:
					opponent = match_data["nextPlayer"]
					opponent_sum = self.card_sum(match_data["players"][players[opponent]])
					
					match_data["nextPlayer"] = (match_data["nextPlayer"] + 1) % len(players)
					next_player_sum = self.card_sum(match_data["players"][players[match_data["nextPlayer"]]])
					
					match_data["matchActive"] = int(time.time())
					
					self.add_status("%s stands at %d. It's %s's turn with %d." % (players[opponent], opponent_sum, players[match_data["nextPlayer"]], next_player_sum))
					
					with open("%s/%s" % (self.matches_path, filename), "w", encoding="utf-8") as file:
						json.dump(match_data, file, ensure_ascii=False, sort_keys=True, indent="\t")
			else:
				self.add_status("It's not your turn yet")
				return
			
		else:
			# existing match! hit!
			try:
				with open("%s/%s" % (self.matches_path, filename)) as file_content:
					match_data = json.load(file_content)
			except:
				self.add_status("This match is not currently running. Start a new one?")
				return
			
			drawn_cards = [];
			for player in players:
				drawn_cards = match_data["players"][player] + drawn_cards
				
			drawn_cards = sorted(drawn_cards)
			
			remaining_cards = set(self.deck_keys) - set(drawn_cards)
			remaining_cards = sorted(remaining_cards)
			
			self.deck_keys = remaining_cards

			if players[match_data["nextPlayer"]] == self.user1:
				# drawing for user1
				
				if players[match_data["nextPlayer"]] in match_data["stand"]:
					# player has quit drawing, skip!
					self.add_status("%s is standing." % players[match_data["nextPlayer"]])
					
				else:
					# draw a card
					card_index = self.draw()
					card_name = self.card_name(card_index)
					
					self.add_status("Player %s drew %s," % (self.user1, card_name))
					match_data["players"][self.user1].append(card_index)
					
					# detect win condition
					sum = self.card_sum(match_data["players"][self.user1])
					if sum > self.winvalue:
						try:
							os.remove("%s/%s" % (self.matches_path, filename))
						except:
							self.add_status("Could not delete match data file!")
							return
						
						self.add_status("%s lost with %d!" % (self.user1, sum))
						return
				
					self.add_status("Sum: %s" % (sum))
					
					match_data["nextPlayer"] = (match_data["nextPlayer"] + 1) % len(players)
					match_data["matchActive"] = int(time.time())
					
					self.add_status("It's %s's turn!" % players[match_data["nextPlayer"]])
					
					with open("%s/%s" % (self.matches_path, filename), "w", encoding="utf-8") as file:
						json.dump(match_data, file, ensure_ascii=False, sort_keys=True, indent="\t")
				
			else:
				self.add_status("It's not your turn yet")
				return
			