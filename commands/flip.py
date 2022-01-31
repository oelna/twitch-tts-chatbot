import random

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	flip = random.randint(0,1)
	result_string = "Heads" if flip != 0 else "Tails"

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
