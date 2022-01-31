import random

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !random <lower limit> <upper limit>, default 1-100"

	if len(command) > 2:
		try:
			result_string = random.randint(int(command[1]),int(command[2]))
		except:
			pass
	elif len(command) == 1:
		result_string = random.randint(1,100)

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
