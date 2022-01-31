async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	if not parent.sounds:
		return False
	
	# output available sound commands
	free_sounds = []
	sub_sounds = []

	for key in parent.sounds:
		sound = parent.sounds[key]
		if sound.get('disabled') != True:
			if sound.get('sub_only') == True:
				sub_sounds.append(key)
			else:
				free_sounds.append(key)

	try:
		await parent.message('Available sounds for all: !%s' % ' !'.join(free_sounds))
		await parent.message('Available sounds for subscribers: !%s' % ' !'.join(sub_sounds))
	except:
		# error
		pass
