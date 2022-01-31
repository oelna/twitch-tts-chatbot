async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = ('hier findest du alles Relevante zum Kurs INT:'
		' https://arnorichter.de/hsma/int/intro'
	)

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
