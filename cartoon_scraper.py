from bs4 import BeautifulSoup
from timeit import default_timer as timer
import datetime
import requests
import logging
import urllib2
import base64
import random
import json
import time
import sys
import re
import os

import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

def soup_request(url):
	logging.info("Requesting {}\n".format(url))
	r = requests.get(url)
	if r.status_code == 200:
		return BeautifulSoup(r.content, 'html.parser')
	else:
		return r.status_code

def show_directory(show):
	if not os.path.exists(show):
		logging.info("Creating {} directory".format(show))
		os.makedirs(show)
	logging.info("Changing to {} directory\n".format(show))
	os.chdir(show)

def get_vars(script):
	script = script[33:]
	script = script.split(".forEach")
	base_range = script[1].split(")) - ")
	base_range = re.sub('[^0-9]', '', base_range[1])
	script = script[0][:-6]
	script = script.replace('"', "")
	script = script.split(", ")
	return extract_iframe(script, int(base_range))

def extract_iframe(js, base_range):
	decoded_string = ""
	for value in js:
		value = base64.b64decode(value)
		value = re.sub('[^0-9]', '', value)
		value = int(value) - base_range
		value = ''.join(map(unichr, [value]))
		decoded_string += value
	decoded_string = decoded_string.split('"')
	return decoded_string

# Extract video hosting endpoint from iframe location
def iframe_looper(scripts):
	for script in scripts:
		if "src:" in str(script):
			script = str(script)
			front = script.index("src:") + 6
			back = script.index("'}]);")
			return script[front:back]

# Extract embedded Javascript from first request
def landing_loop(scripts):
	for script in scripts:
		if len(str(script).split('", "')) > 170:
			return get_vars(str(script))

def get_episodes(show_name, start_season, seasons, start_episode, episodes):
	logging.info("{}: season{}, episodes{}\n".format(show_name, " "+str(start_season) if seasons == 1  else "s "+str(start_season)+"-"+str(start_season+seasons-1), " "+str(start_episode) if episodes == 1  else "s "+str(start_episode)+"-"+str(start_episode+episodes-1)))
	show_directory(show_name)
	url_1 = '{}{}-season-{}-episode-{}'
	show = {
		"show_name": show_name,
		"episodes" : [],
		"began": str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
	}
	for season in range(start_season, start_season + seasons):
		for episode in range(start_episode, start_episode + episodes):
			episode_dict = {
				"episode_season": season,
				"episode_number": episode,
				"requested": str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
			}
			logging.info("Season {} Episode {}\n".format(season, episode))
			first_soup = soup_request(url_1.format(url_base, show_name, season, episode))
			try:
				landing_scripts = first_soup.select("script")
			except:
				logging.error("Returned status code {}\n\n".format(first_soup))
				episode_dict['url'] = url_1
				episode_dict['error_landing'] = first_soup
				continue				
			iframe = landing_loop(landing_scripts)
			url_2 = "https://www.watchcartoononline.io{}".format(iframe[3])
			try:
				name = url_2[url_2.index("{}.".format(episode)) + 2 : -1 * (len(url_2[url_2.index("{}.".format(episode))+2:]) - re.search("[0-9]", url_2[url_2.index("{}.".format(episode))+2:]).start())]
			except Exception as e:
				name = re.sub('[0-9]', '', url_2[url_2.index("=") + 1 : -1 * (len(url_2[url_2.index("=") + 1:]) - url_2[url_2.index("=") + 1:].index("&"))]).replace("%", '')
			except:
				name = ''
			second_soup = soup_request(url_2)
			try:
				video_scripts = second_soup.select("script")
			except:
				logging.error("Returned status code {}\n\n".format(first_soup))
				episode_dict['url'] = url_2
				episode_dict['error_iframe'] = video_scripts
				continue
			url_3 = iframe_looper(video_scripts)
			episode_dict["url"] = url_3.replace("lbb.", "media4.")
			episode_dict["file_name"] = "{}.{}-{}_{}.mp4".format(season, episode, show_name, name)
			episode_dict = write_mp4(episode_dict)
			show["episodes"].append(episode_dict)
	return show

def write_mp4(episode):
	try:
		logging.info("Retrieving mp4 from {}\n".format(episode["url"]))
		response = urllib2.urlopen(episode["url"])
		with open(episode['file_name'], 'wb') as f:
			start = timer()
			logging.info("Writing {}\n{}".format(episode["file_name"], datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
			f.write(response.read())
			end = timer()
			episode["time_elapsed"] = end - start
			logging.info("Writing completed in {} seconds\n\n".format(episode["time_elapsed"]))
	except Exception as e:
		logging.error("Error writing {}\n{}\n\n".format(episode["file_name"], e))
		episode["error_mp4"] = str(e)
		pass
	return episode

def log_data(data):
	data["ended"] = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
	log_name = "cartoon_logs.json"
	logging.info("Changing to parent directory")
	os.chdir("..")
	append = True
	if not os.path.exists("./{}".format(log_name)):
		with open(log_name, "w") as f:
			append = False
	with open(log_name, "r+") as f:
		logging.info("Dumping json data to {}".format(log_name))
		if append:
			existing_data = f.read()
			f.seek(0)
			f.write(existing_data[:-2])
			f.write(",\n")
		else:
			f.write("[\n")
		json.dump(data, f, indent=4, sort_keys=True)
		f.truncate()
		f.write("\n]")
	logging.info("Goodbye")

url_base = "https://www.watchcartoononline.io/"

if __name__ == '__main__':
	shows_data = get_episodes('', 10, 1, 8, 1)
	log_data(shows_data)
