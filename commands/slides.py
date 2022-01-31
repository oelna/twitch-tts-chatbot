async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = ('Präsentations-Folien zu INT: '
		'https://arnorichter.de/hsma/int/slides '
		'und zu HTML: '
		'https://arnorichter.de/hsma/html'
	)

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
