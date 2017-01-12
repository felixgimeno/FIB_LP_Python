#!/usr/bin/python3
from datetime import timedelta, datetime
from ast import literal_eval
import argparse
import urllib.request
import xml.etree.ElementTree
import re
import string
from math import sin, cos, acos, sqrt, atan2, radians, pi

def clean_string(s):
	return s.lower().translate(str.maketrans("àáéèìíïòóùú","aaeeiiioouu"))

class Event:
	def __init__(self, xml_iter):
		def safe_find(b):
			c = xml_iter.find(b)
			if c is None:
				return ""
			else:
				return clean_string(c.text)
		def get_float(a):
			if a != "":
				return float(a)
			return 0
		def get_date(d):
			if d != "":
				return  datetime.strptime(d, '%d/%m/%Y')
			return ""				
		self.lat = get_float(safe_find('gmapx'))
		self.lon = get_float(safe_find('gmapy'))
		self.p_d = get_date(safe_find('proxdate'))
		self.name = safe_find('name')
		self.hour = safe_find('proxhour')
		self.address = safe_find('address')
		self.name_place = safe_find('institutionname')

	def validate(self, debug):
		if self.lat == 0:
			if debug: print("invalid lat")
			return False
		if self.lon == 0:
			if debug: print("invalid lon")
			return False
		if self.p_d == "":
			if debug: print("invalid p_d")
			return False
		if self.name == "":
			if debug: print("invalid name")
			return False
		if self.hour == "":
			if debug: print("invalid hour")
			return False
		if self.address == "":
			if debug: print("invalid address")
			return False
		if self.name_place	== "":
			if debug: print("invalid name_place")
			return False			
		return True

	def satisfies_dates(self, d):
		if isinstance(d, str): 
			return self.p_d == datetime.strptime(d, '%d/%m/%Y')
		if isinstance(d, tuple):
			dt = datetime.strptime(d[0], '%d/%m/%Y')
			def between(a,b,c):
				return a >= min(b,c) and a <= max(b,c)
			a = ((self.p_d - dt).total_seconds())/(60*60*24)
			b = int(d[1])
			c = int(d[2])
			return between(a,b,c)
		if isinstance(d, list):
			return any(self.satisfies_dates(d2) for d2 in d)
		return False
	def satisfies_keys(self, k):
		#caso base
		if isinstance(k, str): 
			return re.search(k, self.name) or re.search(k, self.name_place)
		#caso inductivo lista, AND
		if isinstance(k, list): 
			return all(self.satisfies_keys(k2) for k2 in k)
		#caso inductivo tupla, OR
		if isinstance(k, tuple):
			return any(self.satisfies_keys(k2) for k2 in k)
		return False

class Station:
	def __init__(self, xml_iter):
		def safe_find(b):
			c = xml_iter.find(b)
			if c is None:
				return ""
			else:
				return (c.text).lower()
		def get_float(a):
			if a != "":
				return float(a)
			return 0
		self._id = get_float(safe_find('id'))
		self.lat = get_float(safe_find('lat'))
		self.lon = get_float(safe_find('long'))
		self.slots = get_float(safe_find('slots')) > 0
		self.bikes = get_float(safe_find('bikes')) > 0

class Parking:
	def __init__(self, xml_iter):
		def safe_find(b):
			c = xml_iter.find(b)
			if c is None:
				return ""
			else:
				return (c.text).lower()
		def get_float(a):
			if a != "":
				return float(a)
			return 0
		self._id = get_float(safe_find('id'))
		self.lat = get_float(safe_find('gmapx'))
		self.lon = get_float(safe_find('gmapy'))

def get_distance(lat1, lon1, lat2, lon2):
    degrees_to_radians = pi/180.0
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
    theta1 = lon1*degrees_to_radians
    theta2 = lon2*degrees_to_radians
    _cos = (sin(phi1)*sin(phi2)*cos(theta1 - theta2) + cos(phi1)*cos(phi2))
    return acos(_cos) * 6373

def	print_html_header():
	return "<html><head><meta charset=\"utf-8\"/><title>Practica Python LP Tardor 2016 Felix Axel Gimeno Gil</title></head><body><table border=\"1\"><center>"
	
def print_event(e):
	i = "<tr><td>"
	a = "</td><td>"
	b = "</td></tr>"
	return i+"evento"+a+e.name[:50]+a+e.address+a+str(e.p_d.day)+"/"+str(e.p_d.month)+"/"+str(e.p_d.year)+a+e.hour+b
	
def print_html_slots(e,stations):
	l = sorted(filter(lambda x: x.slots and get_distance(e.lat,e.lon,x.lat,x.lon) < 5000, stations), key=lambda x: get_distance(e.lat,e.lon,x.lat,x.lon))
	l = l[:5]
	ret = ""
	for i in l:
		ret += "<tr><td>bicing aparcable</td>"+"<td>"+str(int(i._id))+"</td>"
		#ret += "<td>"+str(get_distance(e.lat,e.lon,i.lat,i.lon))+"</td>"
		ret += "</tr>"
	return ret	

def print_html_bikes(e,stations):
	l = sorted(filter(lambda x: x.bikes and get_distance(e.lat,e.lon,x.lat,x.lon) < 5000 , stations), key=lambda x: get_distance(e.lat,e.lon,x.lat,x.lon))
	l = l[:5]
	ret = ""
	for i in l:
		ret += "<tr><td>bicing con bicis</td>"+"<td>"+str(int(i._id))+"</td"+"</tr>" 
	return ret

def print_html_parkings(e,parkings):
	l = sorted(filter(lambda x: get_distance(e.lat,e.lon,x.lat,x.lon) < 5000 , parkings), key=lambda x: get_distance(e.lat,e.lon,x.lat,x.lon))
	l = l[:5]
	ret = ""
	for i in l:
		if i._id != 0: ret += "<tr><td>parking disponible</td>"+"<td>"+str(int(i._id))+"</td"+"</tr>" 
	return ret

def print_html_row(e, stations, parkings):
	ret = print_event(e)
	ret += print_html_slots(e,stations)
	ret += print_html_bikes(e,stations)
	ret += print_html_parkings(e,parkings)
	return ret
	
def	print_html_footer():
	return "</center></table></div></body></html>"

if __name__ == '__main__':
	debug = False
	load_from_url = True

	parser = argparse.ArgumentParser(description='Process some data.')

	def process_string(s):
		return literal_eval(clean_string(s))

	parser.add_argument('--key', dest='keys', type=process_string, help='values to filter')
	parser.add_argument('--date', dest='date', type=process_string, help='values to filter')

	args = parser.parse_args()
	if debug: print(args.keys)
	if debug: print(args.date)

	url_events = "http://www.bcn.cat/tercerlloc/agenda_cultural.xml"
	url_stations = "http://wservice.viabicing.cat/getstations.php?v=1"
	url_parkings = "http://www.bcn.cat/tercerlloc/Aparcaments.xml"

	def get_xml(url):
		return xml.etree.ElementTree.fromstring(urllib.request.urlopen(url).read())

	def load_or_read(url, filename):
		if load_from_url:
			root_xml = get_xml(url)
			xml.etree.ElementTree.ElementTree(root_xml).write(filename)
			return root_xml
		return  xml.etree.ElementTree.parse(filename).getroot()
						
	xml_events = load_or_read(url_events, 'events.xml')
	xml_stations = load_or_read(url_stations, 'stations.xml')
	xml_parkings = load_or_read(url_parkings, 'parkings.xml')

	if debug: print(xml_events)
	if debug: print(xml_stations)
	if debug: print(xml_parkings)

	l = []
	for e in xml_events.iter('item'):
		if e.find('gmapx') is not None and e.find('proxdate') is not None:
			w = Event(e)
			if w.validate(debug):
				if args.keys is not None and not w.satisfies_keys(args.keys):
					continue
				if args.date is not None and not w.satisfies_dates(args.date):
					continue	
				l.append(w)

	events = l
	stations = list(map(Station, xml_stations.iter('station')))
	parkings = list(map(Parking, xml_parkings.iter('item'))) 

	if debug: 
		print(len(l))
		print(len(stations))
		print(len(parkings))

	f = open('output.html','w')
	html = ""
	html += print_html_header()
	for e in events:
		html += print_html_row(e, stations, parkings)
	html += print_html_footer()
	f.write(html)
	f.close()
