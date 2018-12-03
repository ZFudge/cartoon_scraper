from bs4 import BeautifulSoup
import datetime
import requests
import logging
import base64
import random
import json
import time
import sys
import re

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
	r = requests.get(url)
	return BeautifulSoup(r.content, 'html.parser')

def get_show_urls(show_name, start_season, seasons, start_episode, episodes):
	logging.info("{}: seasons {}-{}, episodes {}-{}\n".format(show_name, start_season, start_season + seasons - 1, start_episode, start_episode + episodes - 1))
	url = 'https://www.watchcartoononline.io/{}-season-{}-episode-{}'
	show = {
		"show_name": show_name,
		"urls" : []
	}
	for season in range(start_season, start_season + seasons):
		for episode in range(start_episode, start_episode + episodes):
			logging.info("Season {} Episode {}".format(season, episode))
			logging.info("{}\n".format(datetime.datetime.now()))
			first_soup = soup_request(url.format(show_name, season, episode))
			landing_scripts = first_soup.select("script")
			iframe = landing_loop(landing_scripts)
 			# Call iframe
			try:
				url_2 = "https://www.watchcartoononline.io{}".format(iframe[3])
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
				"url":	url_3.replace("lbb.", "media4.")
			})
			time.sleep(round(random.uniform(7, 16), 3))
	return show

def list_urls(show_dict):
	content = ""
	show_name = show_dict["show_name"].split("-")
	for i, n in enumerate(show_name): show_name[i] = "{}{}".format(n[:1].upper(), n[1:])
	show_name = " ".join(show_name)
	for show in show_dict["urls"]:
		content += "{} - Season {} Episode {}\n".format(show_name, show["season"], show["episode"])
		content += show["url"] + "\n\n"
	write_output(content, "a")

def format_urls(show_dict):
	js = "(function o(arr, index = 0) {\n"
	js += 'window.open(arr[index], "_blank")\n'
	js += "setTimeout(() => (index < arr.length - 1) ? o(arr, index + 1) : null, Math.round(Math.random() * 7000 + 13000))"
	js += "}([\n"
	for url in show_dict["urls"]:
		js += '\t"{}",\n'.format(url["url"])
	js = js[:-2] + "\n"
	js += "]))\n\n"
	write_output(js, "w")
	show_dict["javascript"] = js
	return show_dict

def write_output(content, mode):
	file = open("logs.txt", mode)
	file.write(content)
	file.close()

def log_data(data):
	with open("cartoon_logs.json", "a") as f:
	    json.dump(data, f)

if __name__ == '__main__':
	urls = get_show_urls("", 2, 1, 1, 2)
	urls = format_urls(urls)
	list_urls(urls)
	log_data(urls)
