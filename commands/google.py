import urllib.parse

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !google <search terms>, eg: !google african elephant"

	if len(command) > 1:
		result_string = ('Here is your Google search:'
			' https://www.google.com/search?q=%s' % urllib.parse.quote_plus(" ".join(command[1:]))
		)

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
