async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !kb <keybase username>, eg: !kb oelna"

	if len(command) > 1:
		result_string = ('Link to Keybase profile:'
			' https://keybase.io/%s' % command[1]
		)

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
