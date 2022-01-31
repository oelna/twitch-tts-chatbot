import random

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !chance <number> in <number>, eg. !chance 1 in 5"
	if len(command) > 3:
		try:
			percentage = round((int(command[1])/int(command[3])*100),2)
			result = random.randint(int(command[1]),int(command[3]))
			result_string = "%s (%s%%)" % (result, percentage)
		except:
			# error handling chat command
			pass

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
