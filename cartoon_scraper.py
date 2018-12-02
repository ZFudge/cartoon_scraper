from bs4 import BeautifulSoup
import requests
import base64
import random
import time
import re

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
		v = base64.b64decode(value)
		v = re.sub('[^0-9]', '', v)
		v = int(v) - base_range
		v = ''.join(map(unichr, [v]))
		decoded_string += v
	decoded_string = decoded_string.split('"')
	return decoded_string

def frame_looper(scripts):
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

def get_show_urls(show, start_season, end_season, start_episode, end_episode):
	url = 'https://www.watchcartoononline.io/{}-season-{}-episode-{}'
	urls = []
	
	for x in range(start_season, end_season + 1):
		for y in range(start_episode, end_episode + 1):
			first_soup = soup_request(url.format(show, x, y))
			landing_scripts = first_soup.select("script")
			frame = landing_loop(landing_scripts)
 
			url_2 = "https://www.watchcartoononline.io{}".format(frame[3])			
			second_soup = soup_request(url_2)
			video_scripts = second_soup.select("script")

			url_3 = frame_looper(video_scripts)
			urls.append(url_3.replace("lbb.", "media4."))
			time.sleep(round(random.uniform(10, 19), 3))
	return urls

def list_urls(urls):
	for url in urls:
		print url + "\n"

def log_urls(urls):
	js = "[\n"
	for url in urls:
		js += '\t"{}",\n'.format(url)
	js = js[:-2] + "\n"
	js += '].forEach(function(url) {\n'
	js += '\twindow.open(url, "_blank")\n'
	js += '});'
	print js


def main():
	urls = get_show_urls("", 4, 4, 1, 5)
	list_urls(urls)
	log_urls(urls)

main()
