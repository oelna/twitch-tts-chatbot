import os

async def init(parent, message, command=[], params=[]):

	path = os.path.dirname(os.path.realpath(__file__))
	files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

	files.sort()

	result_string = "available commands are: "

	for file in files:
		filename = os.path.splitext(os.path.basename(file))[0]
		if not filename.startswith("_") or filename.startswith("."):
			result_string = "%s !%s" % (result_string, filename)

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
