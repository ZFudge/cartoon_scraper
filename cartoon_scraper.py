from bs4 import BeautifulSoup
import datetime
import requests
import logging
import urllib2
import base64
import random
import json
import sys
import re
import os

import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

def soup_request(url):
	logging.info("Requesting {}\n".format(url))
	r = requests.get(url)
	return BeautifulSoup(r.content, 'html.parser')

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

def iframe_looper(scripts):
	for script in scripts:
		if "src:" in str(script):
			script = str(script)
			front = script.index("src:") + 6
			back = script.index("'}]);")
			return script[front:back]

def landing_loop(scripts):
	for script in scripts:
		if len(str(script).split('", "')) > 170:
			return get_vars(str(script))

def get_episodes(show_name, start_season, seasons, start_episode, episodes):
	logging.info("{}: seasons {}-{}, episodes {}-{}\n".format(show_name, start_season, start_season + seasons - 1, start_episode, start_episode + episodes - 1))
	show_directory(show_name)
	url_1 = 'https://www.watchcartoononline.io/{}-season-{}-episode-{}'
	show = {
		"show_name": show_name,
		"urls" : []
	}
	for season in range(start_season, start_season + seasons):
		for episode in range(start_episode, start_episode + episodes):
			logging.info("Season {} Episode {}\n".format(season, episode))
			first_soup = soup_request(url_1.format(show_name, season, episode))
			landing_scripts = first_soup.select("script")
			iframe = landing_loop(landing_scripts)
 			# Call iframe
			try:
				url_2 = "https://www.watchcartoononline.io{}".format(iframe[3])
				try:
					name = url_2[url_2.index("{}.".format(episode)) + 2 : -1 * (len(url_2[url_2.index("{}.".format(episode))+2:]) - re.search("[0-9]", url_2[url_2.index("{}.".format(episode))+2:]).start())]
				except Exception as e:
					name = re.sub('[0-9]', '', url_2[url_2.index("=") + 1 : -1 * (len(url_2[url_2.index("=") + 1:]) - url_2[url_2.index("=") + 1:].index("&"))]).replace("%", '')
				except:
					name = ''
			except:
				logging.error("Error on Season {} Episode {}".format(season, episode))
				logging.error("{}\n\n".format(iframe))
				continue
			second_soup = soup_request(url_2)
			video_scripts = second_soup.select("script")
			# Extract hosting endpoint 
			url_3 = iframe_looper(video_scripts)
			file_name = '{}.{}-{}_{}.mp4'.format(season, episode, show_name, name)
			episode_dict = {
				"season": season,
				"episode": episode,
				"url":	url_3.replace("lbb.", "media4."),
				"name": name
			}
			show["urls"].append(episode_dict)
			write_mp4(episode_dict["url"], file_name)
	return show

def write_mp4(url, file_name):
	try:
		logging.info("Retrieving mp4 from {}\n".format(url))
		response = urllib2.urlopen(url)
		with open(file_name, 'wb') as f:
			logging.info("Writing {}".format(file_name))
			f.write(response.read())
			logging.info("Writing complete\n\n")
	except:
		logging.error("Error writing {}\n\n".format(file_name))
		pass

def log_data(data):
	log_name = "cartoon_logs.json"
	logging.info("Changing to parent directory")
	os.chdir("..")
	with open(log_name, "a") as f:
		logging.info("Dumping json data to {}".format(log_name))
		f.write(",\n")
		json.dump(data, f, indent=4, sort_keys=True)
	logging.info("Goodbye")

if __name__ == '__main__':
	urls = get_episodes(shows[3], 1, 1, 1, 1)
	log_data(urls)
