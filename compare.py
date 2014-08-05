import cssutils
import os
import config
import fnmatch
import re
import sys
from pprint import pprint
import getopt

def getFileNames():
	css_file = [f for f in os.listdir(config.FILE_DIR) if fnmatch.fnmatch(f, '*.css')]
	filenames = filter(re.compile(config.FILE_REGEX).match, css_file)
	return filenames


def findSelectorIndex(selector, array):
	for rule in array:
		if (rule['type'] == 'style' and rule['selector'] == selector) or (rule['type'] == 'media' and rule['query'] == selector):
			return array.index(rule)
	return -1


def appendValue(prop, value, target, index):
	if prop in (target[index]['declarations']):
		i = added = 0
		values = target[index]['declarations'][prop]
		while i <  len(values):
			if values[i][1] == value:
				target[index]['declarations'][prop][i][0] = values[i][0] + 1
				added = 1
				break
			i = i + 1
		if added == 0:
			target[index]['declarations'][prop].append([1, value])
	else:
		target[index]['declarations'][prop]= [[1, value]]

def readStyle(rule, target):
	selector = str(rule.selectorText)
	declarations = rule.style
	index = findSelectorIndex(selector, target)
	if index >= 0:
		for property in declarations.keys():
			value = str(declarations[property])
			prop = str(property)
			appendValue(prop, value, target, index)
	else:
		rule = {
			'type': 'style',
			'selector': selector,
			'declarations': {}
		}

		for property in declarations.keys():
			value = str(declarations[property])
			prop = str(property)
			rule['declarations'][prop] = [[1, value]]

		target.append(rule)

def readMedia(rule, target):
	query = str(rule.media.mediaText)
	children = rule.cssRules
	index = findSelectorIndex(query, target)
	if index >= 0:
		for rule in children:
			if rule.type == rule.STYLE_RULE and isinstance(rule, cssutils.css.CSSStyleRule):
				readStyle(rule, target[index]['children'])
	else:
		query = {
			'type': 'media',
			'query': query,
			'children': []
		}

		for rule in children:
			if rule.type == rule.STYLE_RULE and isinstance(rule, cssutils.css.CSSStyleRule):
				readStyle(rule, query['children'])

		target.append(query)


def readCSS(stylesheet, target):
	for rule in stylesheet:
		if rule.type == rule.MEDIA_RULE and isinstance(rule, cssutils.css.CSSMediaRule):
			readMedia(rule, target)
		elif rule.type == rule.STYLE_RULE and isinstance(rule, cssutils.css.CSSStyleRule):
			readStyle(rule, target)				

def postProcess(output):
	curr = 0
	total = len(output)
	for rule in output:
		if rule['type'] == 'style':
			for key in rule['declarations'].keys():
				rule['declarations'][key] = [len(rule['declarations'][key]), rule['declarations'][key]]
			
		elif rule['type'] == 'media':
			for child in rule['children']:
				for key in child['declarations'].keys():
					child['declarations'][key] = [len(child['declarations'][key]), child['declarations'][key]]

		sys.stdout.write("\rprocessing: " + ("%.2f" % (100.0 * curr / total)) + '%')
		sys.stdout.flush()

def compare(output_file):
	filenames = getFileNames()
	output = []
	curr = 0
	total = len(filenames)
	for fn in filenames:
		# print fn
		path = os.path.join('css', fn)
		stylesheet = cssutils.parseFile(path, validate=False)
		readCSS(stylesheet, output)
		curr += 1
		sys.stdout.write("\rcomparing: " + ("%.2f" % (100.0 * curr / total)) + '%')
		sys.stdout.flush()
	
	postProcess(output)
	# output = pprint(output)
	with open(output_file, 'wt') as out:
		pprint(output, stream=out)
	sys.stdout.write("\nmission completed :)")


#######################################################################
# Main
#######################################################################

def usage():
    print "usage: " + sys.argv[0] + " -o output-file"

output_file = None
try:
    opts, args = getopt.getopt(sys.argv[1:], 'o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-o':
        output_file = a
    else:
        pass # no-op
if output_file == None:
    usage()
    sys.exit(2)

compare(output_file)
