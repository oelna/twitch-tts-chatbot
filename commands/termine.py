async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = 'Semestertermine HS Mannheim: https://www.hs-mannheim.de/studierende/termine-news-service/semestertermine.html'

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
