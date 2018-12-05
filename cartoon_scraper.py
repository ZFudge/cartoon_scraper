from bs4 import BeautifulSoup
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

def soup_request(url):
	logging.info("{}\n".format(datetime.datetime.now()))
	logging.info(url)
	r = requests.get(url)
	return BeautifulSoup(r.content, 'html.parser')

def get_show_urls(show_name, start_season, seasons, start_episode, episodes):
	logging.info("{}: seasons {}-{}, episodes {}-{}\n".format(show_name, start_season, start_season + seasons - 1, start_episode, start_episode + episodes - 1))
	url_1 = 'https://www.watchcartoononline.io/{}-season-{}-episode-{}'
	show = {
		"show_name": show_name,
		"urls" : []
	}
	for season in range(start_season, start_season + seasons):
		for episode in range(start_episode, start_episode + episodes):
			logging.info("Season {} Episode {}".format(season, episode))
			first_soup = soup_request(url_1.format(show_name, season, episode))
			landing_scripts = first_soup.select("script")
			iframe = landing_loop(landing_scripts)
 			# Call iframe
			try:
				url_2 = "https://www.watchcartoononline.io{}".format(iframe[3])
				try:
					name = url_2[url_2.index("{}.".format(episode)) + 2 : -1 * (len(url_2[url_2.index("{}.".format(episode))+2:]) - re.search("[0-9]", url_2[url_2.index("{}.".format(episode))+2:]).start())]
				except:
					name = re.sub('[0-9]', '', url_2[url_2.index("=") + 1 : -1 * (len(url_2[url_2.index("=") + 1:]) - url_2[url_2.index("=") + 1:].index("&"))]).replace("%", '')
				except:
					name = ''
			except:
				logging.error("Error on Season {} Episode {}".format(season, episode))
				logging.error(iframe)
				sys.exit()
			second_soup = soup_request(url_2)
			video_scripts = second_soup.select("script")
			# Extract hosting endpoint 
			url_3 = iframe_looper(video_scripts)
			show["urls"].append({
				"season": season,
				"episode": episode,
				"url":	url_3.replace("lbb.", "media4."),
				"name": name
			})
			time.sleep(round(random.uniform(7, 16), 6))
	return show

def log_data(data):
	with open("cartoon_logs.json", "a") as f:
	    json.dump(data, f)

def write_mp4s(show_dict):
	if not os.path.exists(show_dict['show_name']):
		logging.info("Creating {} directory".format(show_dict['show_name']))
		os.makedirs(show_dict['show_name'])
	os.chdir(show_dict['show_name'])
	logging.info("Changing to {} directory".format(show_dict['show_name']))
	for url in show_dict['urls']:
		file_name = '{}.{}-{}-{}.mp4'.format(url['season'], url['episode'], show_dict['show_name'], url["name"])
		write_mp4(url, file_name)

def write_mp4(url, file_name):
	try:
		logging.info("\n\n{}\n".format(datetime.datetime.now()))
		logging.info(url["url"])
		response = urllib2.urlopen(url["url"])
		with open(file_name, 'wb') as f:
			logging.info("Writing {}".format(file_name))
			f.write(response.read())
			f.close()
			time.sleep(round(random.uniform(7, 14), 6))
	except:
		pass

if __name__ == '__main__':
	urls = get_show_urls("", 2, 1, 1, 1)
	log_data(urls)
	write_mp4s(urls)
