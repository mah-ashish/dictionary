# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json

def get_synonyms(description):
	try:
		synonyms_tag = description.select('.synonyms > .exg > .exs')[0]
		first = synonyms_tag.strong.extract()
		first = first.text
		synonyms_text = synonyms_tag.text
		synonyms_text = [synonym for synonym in synonyms_text.split(', ') if synonym!='']
		synonyms_text = [first] + synonyms_text
		return synonyms_text
	except:
		return []

def get_entryHead_content(tag):

	try:
		value = tag.select('header > .hwg > .hw')[0].text
		return value
	except:
		return None

def get_gramb_content(tag):
	
	meaning = {}
	try:
		pos = tag.select('span[class="pos"]')[0].text

		description_list = tag.select('ul[class="semb"] > li > .trg')

		pos_results = []
		for description in description_list:
			description_results = {}
			try:
				definition = description.select('p > .ind')[0].text
			except:
				definition = None

			try:
				example = description.select('.exg > .ex > em')[0].text
				example = example.replace(u'\u2018', '').replace(u'\u2019', '')
			except:
				example = None

			synonyms = get_synonyms(description)

			if not definition and not example and not synonyms:
				continue

			if definition:
				description_results['definition'] = definition
			if example:
				description_results['example'] = example
			if synonyms:
				description_results['synonyms'] = synonyms

			pos_results.append(description_results)

		meaning[pos] = pos_results

		return meaning

	except:
		return None

def get_pronSection_content(tag):
	
	try:
		phonetic = tag.select('span[class="phoneticspelling"]')[0].text
		pronunciation = tag.select('audio')[0]['src']
		return phonetic, pronunciation
	except:
		print(tag.select('audio')[0])
		return None

def get_vocabulary(search_word):
	dictionary_page = 'https://en.oxforddictionaries.com/definition/'+search_word
	page = requests.get(dictionary_page,
		headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0"})
	soup = BeautifulSoup(page.text, 'html.parser')
	
	check_validity = soup.select('h2.hwg')
	if not check_validity:
		return None

	result = []
	
	entryWrapper = soup.select('div[class="entryWrapper"]')[0]
	entryHeads = entryWrapper.select('div[class="entryHead primary_homograph"]')

	grambs = entryWrapper.select('section[class="gramb"]')

	pronSections = entryWrapper.select('section[class="pronSection etym"]')

	current_tag = entryHeads[0]

	result = []

	while current_tag:
		if current_tag in entryHeads:
			res = {}
			word = get_entryHead_content(current_tag)
			if word:
				res['word'] = word

			current_tag = current_tag.nextSibling

			while current_tag and current_tag not in entryHeads:
				if current_tag in grambs:
					gramb = get_gramb_content(current_tag)
					if 'meaning' in res:
						temp = res['meaning']
						updated_meaning = {**temp, **gramb}
						res['meaning'] = updated_meaning
					else:
						res['meaning'] = gramb
				elif current_tag in pronSections:
					phonetic, pronunciation = get_pronSection_content(current_tag)
					res['phonetic'] = phonetic
					res['pronunciation'] = pronunciation
				current_tag = current_tag.nextSibling

			meaning = res.pop('meaning', None)
			if meaning:
				res['meaning'] = meaning

			result.append(res)

	return result

#for chrome extension
def get_first_meaning(tag):
	try:
		pos = tag.select('span[class="pos"]')[0].text
		description = tag.select('ul[class="semb"] > li > .trg')[0]
		meaning = description.select('p > .ind')[0].text
		synonyms = get_synonyms(description)
		return meaning, synonyms
	except:
		return None

#for chrome extension
def get_meaning(search_word):
	dictionary_page = 'https://en.oxforddictionaries.com/definition/'+search_word
	page = requests.get(dictionary_page,
		headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0"})
	soup = BeautifulSoup(page.text, 'html.parser')
	
	check_validity = soup.select('h2.hwg')
	if not check_validity:
		return None

	result = []
	
	entryWrapper = soup.select('div[class="entryWrapper"]')[0]
	entryHead = entryWrapper.select('div[class="entryHead primary_homograph"]')[0]

	gramb = entryWrapper.select('section[class="gramb"]')[0]

	pronSection = entryWrapper.select('section[class="pronSection etym"]')[0]

	result = {}

	word = get_entryHead_content(entryHead)
	meaning, synonyms = get_first_meaning(gramb)
	phonetic, pronunciation = get_pronSection_content(pronSection)

	if not word and not not meaning and not phonetic and not pronunciation:
		return None

	if word:
		result['word'] = word

	if meaning:
		result['meaning'] = meaning

	if phonetic:
		result['phonetic'] = phonetic

	if pronunciation:
		result['pronunciation'] = pronunciation

	if synonyms:
		n = len(synonyms)
		if n > 2:
			first = synonyms[0]
			last = synonyms[-1]
			synonyms = [first, last]
		result['synonyms'] = synonyms

	return result