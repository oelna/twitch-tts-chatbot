import random

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !pick <option1> <option2> <option3> …"
	if len(command) > 1:
		try:
			result_string = random.choice(command[1:])
		except:
			# error handling chat command
			pass

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
