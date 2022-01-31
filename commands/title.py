# requires channel:manage:broadcast scope for channel token!

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	if message["mod"] == True or message["broadcaster"] == True:
		try:
			await parent.api_set_stream_title(" ".join(command[1:]), message)
		except:
			await parent.message("Could not set new stream title!")
	else:
		await parent.message("%s Only mods are authorized to use !title" % message["nick"])
