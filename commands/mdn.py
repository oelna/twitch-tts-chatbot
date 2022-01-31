import urllib.parse

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !mdn <html|css> <element|property>, eg: !mdn html li"

	if len(command) > 2:
		if command[1].lower() == 'css':
			result_string = "https://developer.mozilla.org/de/docs/Web/CSS/%s" % urllib.parse.quote_plus(command[2])
		elif command[1].lower() == 'html':
			result_string = "https://developer.mozilla.org/de/docs/Web/HTML/Element/%s" % urllib.parse.quote_plus(command[2])

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
