import requests
import json
import math
from datetime import datetime
from dateutil import relativedelta

async def init(parent, message, command=[], params=[]):
	if parent is None or message is None:
		return

	result_string = "Usage: !following"
	channel = command[1] if len(command) > 1 else parent.config["channel"]["name"]

	url = "https://api.twitch.tv/helix/users/follows"

	credentials = {
		"Authorization": "Bearer %s" % parent.config["channel"]["access_token"],
		"Client-Id": parent.config["channel"]["client_id"]
	}

	parameters = {}
	parameters["from_id"] = int(message["tags"]["user-id"])
	parameters["to_id"] = int(message["tags"]["room-id"])

	try:
		request = requests.get(url, headers=credentials, params=parameters)
	except:
		print('API error')

	if request.status_code == 200:
		response = json.loads(request.text)

		if int(response["total"]) > 0:
			started = datetime.strptime(response["data"][0]["followed_at"], '%Y-%m-%dT%H:%M:%SZ')
			now = datetime.utcnow()
			duration = math.floor((now.timestamp() - started.timestamp()) / 60 / 60 / 24)

			# https://stackoverflow.com/a/32658323
			r = relativedelta.relativedelta(now, started)

			if duration > 365:
				duration_string = '%i years, %i months, %i days' % (r.years, r.months, r.days)
			elif duration > 31:
				duration_string = '%i months, %i days' % (r.months, r.days)
			else:
				duration_string = '%i days' % (r.days)

			result_string = '%s has been following %s for %s' % (response["data"][0]["from_name"], response["data"][0]["to_name"], duration_string)
		else:
			result_string = '%s is not not following %s' % (message["nick"], message["channel"])
	else:
		return None

	try:
		await parent.message(result_string)
	except:
		# error sending result
		pass
