import random

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	if not message["mod"] and not message["broadcaster"]:
		await parent.message("Only mods are authorized to use !test")
		return

	# enable bot test messages
	if len(command) > 1:
		raw_message = ""
		if command[1] == "msg":
			raw_message = "@badge-info=;badges=moderator/1,sub-gift-leader/2;client-nonce=4325e5ca80a53b096fdc31f10baec9f8;color=#D6B1FF;display-name=Liz_Kato;emotes=emotesv2_ee7307a9a1344661b521566a77e97afb:44-53;flags=;id=d83a5c72-090c-400a-a3fa-afd82a1c5628;mod=1;room-id=59039718;subscriber=0;tmi-sent-ts=1633092206308;turbo=0;user-id=156797758;user-type=mod :liz_kato!liz_kato@liz_kato.tmi.twitch.tv PRIVMSG #oelna81 :heißt dann gaming stream in der blockwoche? celtisEyes"
		elif command[1] == "sub":
			raw_message = "@badge-info=subscriber/0;badges=subscriber/0,premium/1;color=#5F9EA0;display-name=FangZzWho;emotes=;flags=;id=1c02c0b1-de97-46d5-9cb5-ea62f54aca5d;login=fangzzwho;mod=0;msg-id=sub;msg-param-cumulative-months=1;msg-param-months=0;msg-param-should-share-streak=0;msg-param-sub-plan-name=Channel\sSubscription\s(oelna81);msg-param-sub-plan=Prime;room-id=71092938;subscriber=1;system-msg=FangZzWho\ssubscribed\swith\sTwitch\sPrime.;tmi-sent-ts=1568505717237;user-id=148323897;user-type= :tmi.twitch.tv USERNOTICE #oelna81 :Hello World!"
		elif command[1] == "resub":
			test_messages = [
				"@badge-info=subscriber/10;badges=subscriber/9,premium/1;color=#42F21C;display-name=Nocturnal_Kemono;emotes=;flags=;id=31438706-3223-4743-ab77-6530f688eb81;login=nocturnal_kemono;mod=0;msg-id=resub;msg-param-cumulative-months=10;msg-param-months=0;msg-param-should-share-streak=0;msg-param-sub-plan-name=Channel\sSubscription\s(xqcow);msg-param-sub-plan=Prime;room-id=71092938;subscriber=1;system-msg=Nocturnal_Kemono\ssubscribed\swith\sTwitch\sPrime.\sThey've\ssubscribed\sfor\s10\smonths!;tmi-sent-ts=1568505665852;user-id=85199016;user-type= :tmi.twitch.tv USERNOTICE #oelna81 :Great stream – keep it up!",
				"@badge-info=subscriber/10;badges=subscriber/9,premium/1;color=#42F21C;display-name=Nocturnal_Kemono;emotes=;flags=;id=31438706-3223-4743-ab77-6530f688eb81;login=nocturnal_kemono;mod=0;msg-id=resub;msg-param-cumulative-months=10;msg-param-months=0;msg-param-should-share-streak=0;msg-param-sub-plan-name=Channel\sSubscription\s(xqcow);msg-param-sub-plan=Prime;room-id=71092938;subscriber=1;system-msg=Nocturnal_Kemono\ssubscribed\swith\sTwitch\sPrime.\sThey've\ssubscribed\sfor\s10\smonths!;tmi-sent-ts=1568505665852;user-id=85199016;user-type= :tmi.twitch.tv USERNOTICE #oelna81"
			]
			raw_message = random.choice(test_messages)
		elif command[1] == "gift":
			raw_message = "@badge-info=;badges=staff/1,premium/1;color=#0000FF;display-name=TWW2;emotes=;id=e9176cd8-5e22-4684-ad40-ce53c2561c5e;login=tww2;mod=0;msg-id=subgift;msg-param-months=1;msg-param-recipient-display-name=Mr_Woodchuck;msg-param-recipient-id=89614178;msg-param-recipient-name=mr_woodchuck;msg-param-sub-plan-name=House\sof\sNyoro~n;msg-param-sub-plan=1000;room-id=19571752;subscriber=0;system-msg=TWW2\sgifted\sa\sTier\s1\ssub\sto\sMr_Woodchuck!;tmi-sent-ts=1521159445153;turbo=0;user-id=13405587;user-type=staff :tmi.twitch.tv USERNOTICE #oelna81"
		elif command[1] == "raid":
			raw_message = "@badge-info=;badges=turbo/1;color=#9ACD32;display-name=Forsen;emotes=;id=3d830f12-795c-447d-af3c-ea05e40fbddb;login=testchannel;mod=0;msg-id=raid;msg-param-displayName=Forsen;msg-param-login=testchannel;msg-param-viewerCount=15;room-id=56379257;subscriber=0;system-msg=15\sraiders\sfrom\sForsen\shave\sjoined\n!;tmi-sent-ts=1507246572675;tmi-sent-ts=1507246572675;turbo=1;user-id=123456;user-type= :tmi.twitch.tv USERNOTICE #oelna81"
		elif command[1] == "bits":
			test_messages = [
				"@badge-info=;badges=staff/1,bits/1000;bits=100;color=;display-name=ronni;emotes=;id=b34ccfc7-4977-403a-8a94-33c6bac34fb8;mod=0;room-id=1337;subscriber=0;tmi-sent-ts=1507246572675;turbo=1;user-id=1337;user-type=staff :ronni!ronni@ronni.tmi.twitch.tv PRIVMSG #oelna81 :cheer100",
				"@badge-info=;badges=staff/1,bits/1000;bits=1600;color=;display-name=ronni;emotes=;id=b34ccfc7-4977-403a-8a94-33c6bac34fb8;mod=0;room-id=1337;subscriber=0;tmi-sent-ts=1507246572675;turbo=1;user-id=1337;user-type=staff :ronni!ronni@ronni.tmi.twitch.tv PRIVMSG #oelna81 :cheer1600"
			]
			raw_message = random.choice(test_messages)
		elif command[1] == "quit":
			if message["broadcaster"]:
				print('Exiting ...')
				await parent.send(parent.connections["irc"]["conn"], 'QUIT')
				sys.exit()
		elif command[1] == "restart":
			if message["broadcaster"]:
				print('Bot is restarting ...')
				await parent.message("Hold on, I'm restarting!")
				await parent.send(parent.connections["irc"]["conn"], "QUIT")
				parent.reconnect()

		if len(raw_message) > 0:
			test_message = parent.parse_message(raw_message)
			await parent.handle_message(test_message)
	else:
		await parent.message("Usage: !test <msg|sub|resub|gift|raid|bits|restart>")
