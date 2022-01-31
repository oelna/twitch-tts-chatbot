import math
from datetime import datetime

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !uptime <channel>"
	channel = command[1] if len(command) > 1 else parent.config["channel"]["name"]

	try:
		data = await parent.api_get_channel_data(channel)
	except:
		pass
	else:
		if len(data) > 0:
			if len(data.get('data')) > 0:
				stream_info = data.get('data')[0]

				started = datetime.strptime(stream_info["started_at"], '%Y-%m-%dT%H:%M:%SZ')
				now = datetime.utcnow().timestamp()
				duration = math.floor((now - started.timestamp()) / 60);

				result_string = '%s has been live for' % channel;

				if duration > 59:
					hours = int(duration / 60);
					minutes = duration % 60;
					result_string = "%s %s hours and %s minutes" % (result_string, hours, minutes);
				else:
					result_string = "%s %s minutes" % (result_string, duration);
			else:
				result_string = '%s is not currently live' % channel;

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
