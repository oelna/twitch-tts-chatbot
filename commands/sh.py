import urllib.parse

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !sh <element|property>, eg: !sh background-color or !sh li"

	if len(command) > 1:
		result_string = "Here is your SelfHTML search: https://wiki.selfhtml.org/index.php?search=%s" % urllib.parse.quote_plus(command[1])

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
