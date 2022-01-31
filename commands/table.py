async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = 'Better Tables: https://i.imgur.com/ZY8dKpA.gif'

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
