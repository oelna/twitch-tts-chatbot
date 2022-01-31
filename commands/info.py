async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = ('Die Streams INT und HTML sind Vorlesungen der Fakultät Design'
		' an der  Hochschule Mannheim. Sie sind an Webdesign-'
		'Neueinsteiger gerichtet. Kommentare und Tips sind gern gesehen,'
		' aber bitte formuliere sie verständlich für Anfänger.'
		' Kursinfo unter !int !html'
	)

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
