import ast
import json
import os
import re
import subprocess
import sys
import urllib2

from HTMLParser import HTMLParser

import utility

reload(sys)
sys.setdefaultencoding("utf-8")

def command_line(args):
    if 'parse' in args or 'parse' in args['argv']:
        if 'url' in args:
            res = parse_url(args['url'])

            print('Links:')
            for link in res.links:
                print(link)
        else:
            print('No url given to parse.')
    elif 'scrape' in args:
        if 'f' in args:
            if 'url' in args:
                url = args['url']

                print(find_data_on_page(url, read_filter_file(args['f'])))
            else:
                print('No url given to scrape.')
        else:
            print('Need a file to define the scraper.')
    elif 'retrieve' in args:
        if 'url' in args:
            url = args['url']

            print(get_page_data(url))
        else:
            print('No url given.')

def run_command(command):
    return subprocess.check_output(command, shell=True)

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def get_page_data(url):
    try:
        resource = urllib2.urlopen(url)
        page_data = resource.read()
        resource.close()

        return page_data
    except:
        return run_command('curl -k -s "{}"'.format(url))

def get_json(url):
    resource = urllib2.urlopen(url)
    page_data = resource.read()
    resource.close()
    data = json.loads(page_data)

    return byteify(data)

def read_filter_file(path):
    contents = []

    with open(path, 'r') as f:
        contents = f.read().replace('\r', '').split('\n')

    filters = []
    for line in contents:
        params = line.split(';', 1)
        params[0] = params[0].strip()

        if params[0] == 'filter':
            data = ast.literal_eval(params[1].strip())

            if isinstance(data, list):
                filters.append(data)
            else:
                filters.append([data])

    return filters

def transpose(l):
    return map(list, zip(*l))

def find_data_on_page(url, filters):
    data = get_page_data(url).replace('\n', '')

    res = []
    for f in filters:
        temp = []
        for part in f:
            # Find all the data that matches this
            temp.append(re.findall(part, data))

        # Assuming there is one for each, transposing should give it to us by row.
        res.append(transpose(temp))

    return res

class Link:
    def __init__(self, href, text, in_parentheses, in_paragraph, in_table, in_tr, in_list, divs=[], div_ids=[], spans=[], span_ids=[], attributes=[]):
        self.href = href
        self.text = text

        self.in_parentheses = in_parentheses
        self.in_paragraph = in_paragraph
        self.in_table = in_table
        self.in_tr = in_tr
        self.in_list = in_list

        self.divs = filter(lambda i: len(i) > 0, divs)
        self.div_ids = filter(lambda i: len(i) > 0, div_ids)
        self.spans = filter(lambda i: len(i) > 0, spans)
        self.span_ids = filter(lambda i: len(i) > 0, span_ids)

        self.attributes = attributes

    def __repr__(self):
        return '{}: {} ({}, {}, {}, {}, {})'.format(self.href, self.text, self.in_parentheses, self.in_paragraph, self.in_table, self.in_tr, self.in_list)

class Parser(HTMLParser):
    def setup(self):
        self.links = []

        self.table_level = 0
        self.tr_level = 0
        self.paragraph_level = 0
        self.list_level = 0
        self.link_level = 0
        self.link_data = ''
        self.link_attrs = []

        self.divs = []
        self.div_ids = []
        self.spans = []
        self.span_ids = []

        self.data = ''

    def search(self, data):
        self.setup()

        self.data = data
        self.parentheses = utility.get_containers(self.data, '(', ')')

        self.feed(data)

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.table_level += 1
        elif tag == 'tr':
            self.tr_level += 1
        elif tag == 'p':
            self.paragraph_level += 1
        elif tag == 'a':
            self.link_level += 1

            self.link_attrs = attrs
        elif tag == 'li':
            self.list_level += 1
        elif tag == 'div':
            self.div_ids.append(self.get_attribute(attrs, 'id'))
            self.divs.append(self.get_attribute(attrs, 'class'))
        elif tag == 'span':
            self.span_ids.append(self.get_attribute(attrs, 'id'))
            self.spans.append(self.get_attribute(attrs, 'class'))

    def handle_data(self, data):
        if self.link_level > 0:
            self.link_data += data

    def handle_endtag(self, tag):
        if tag == 'table':
            self.table_level -= 1
        elif tag == 'tr':
            self.tr_level -= 1
        elif tag == 'p':
            self.paragraph_level -= 1
        elif tag == 'li':
            self.list_level -= 1
        elif tag == 'div':
            self.divs.pop(-1)
            self.div_ids.pop(-1)
        elif tag == 'span':
            self.spans.pop(-1)
            self.span_ids.pop(-1)
        elif tag == 'a':
            self.link_level -= 1

            if self.link_level == 0:
                attrs = self.link_attrs
                self.link_attrs = []

                href = self.get_attribute(attrs, 'href')

                # Check if we're in parentheses.
                in_parentheses = False
                plain_text = self.get_starttag_text()
                for p in self.parentheses:
                    if plain_text in p:
                        in_parentheses = True

                        break

                attributes = {}
                for name, value in attrs:
                    attributes[name] = value

                self.links.append(Link(href, self.link_data, in_parentheses, self.paragraph_level > 0, self.table_level > 0, self.tr_level > 0, self.list_level > 0, divs=self.divs, div_ids=self.div_ids, spans=self.spans, span_ids=self.span_ids, attributes=attributes))

                self.link_data = ''

    def get_attribute(self, attributes, attribute):
        for name, value in attributes:
            if name == attribute:
                return value
        return ''

def parse_url(url, tries=1):
    while tries > 0:
        tries -= 1

        try:
            resource = urllib2.urlopen(url)

            page_data = resource.read()

            parser = Parser()
            href = parser.search(page_data)

            resource.close()

            return parser
        except Exception as e:
            print('Failed!')
            print(e)

            if tries > 0:
                print('Retrying...')

    return None

def get_links(url, tries=1):
    return parse_url(url, tries=tries).links

# Clicks on the first link with an href matching link_pattern or with text matching link_text_pattern
# Any links on the page that return True when f is called with them are added to a list
# Returns the full history, plus the list of matching links
def follow_links(url, f, link_pattern=None, link_text_pattern=None, link_prefix='', verbose=1, fname=None, tries=1):
    pages = [url]

    history = []
    matched_links = []
    matched_link_count = 0

    if fname != None:
        try:
            os.mkdir(fname)
        except:
            pass

    while len(pages) > 0:
        cur_url = pages.pop(0)
        if verbose > 1:
            print('')
            print('Getting links from {}'.format(link_prefix + cur_url))

        old_len = len(matched_links)
        links = get_links(link_prefix + cur_url, tries=tries)
        if verbose > 1:
            print('Got {} links.'.format(len(links)))

        for link in links:
            if (link_pattern != None and re.match(link_pattern, link.href)) or (link_text_pattern != None and re.match(link_text_pattern, link.text)):
                # We don't want to repeat ourselves
                if not link.href in pages and not link.href in history:
                    pages.append(link.href)
            elif f(link):
                matched_links.append(link)

        history.append(cur_url)

        if verbose == 1:
            print('\'{}\': {} matched links (total: {}), {} pages in the history.'.format(cur_url, len(matched_links), matched_link_count, len(history)))
        elif verbose > 1:
            print('{} matched links (total: {}), {} pages in the history.'.format(len(matched_links), matched_link_count, len(history)))

        if fname != None:
            cur_file = cur_url.split('/')[-1].encode(sys.stdout.encoding, errors='replace')[:197]
            cur_file = utility.remove_illegal_path_characters(re.sub(r'[^\x00-\x7F]+', '-', urllib2.unquote(cur_file)))

            with open('{}/{}.txt'.format(fname, cur_file), 'w') as outfile:
                for link in matched_links:
                    outfile.write('{}\n'.format(link.href))

                matched_link_count += len(matched_links)
                matched_links = []
        else:
            matched_link_count = len(matched_links)

    return history, matched_links

if __name__ == '__main__':
    command_line(utility.command_line_args(sys.argv))

