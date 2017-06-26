#!/usr/bin/env python
# Python 2.7.x - 3.6.x
# LinkFinder
# By Gerben_Javado

# Import libraries
import re
import sys
import os
import glob
import cgi
import argparse
import requests
from requests_file import FileAdapter
import jsbeautifier

# Regex used
regex = re.compile(r"""

  ([^\n]*(?:"|')                    # Start newline delimiter

  (?:
    ((?:[a-zA-Z]{1,10}://|//)       # Match a scheme [a-Z]*1-10 or //
    [^"'/]{1,}\.                    # Match a domainname (any character + dot)
    [a-zA-Z]{2,}[^"']{0,})          # The domainextension and/or path

    |

    ((?:/|\.\./|\./)                # Start with /,../,./
    [^"'><,;| *()(%$^/\\\[\]]       # Next character can't be... 
    [^"'><,;|()]{1,})               # Rest of the characters can't be

    |

    ([a-zA-Z0-9/]{1,}/              # Relative endpoint with /
    [a-zA-Z0-9/]{1,}\.[a-z]{1,4}    # Rest + extension
    (?:[\?|/][^"|']{0,}|))          # ? mark with parameters

    |

    ([a-zA-Z0-9]{1,}                # filename
    \.(?:php|asp|aspx|jsp)          # . + extension
    (?:\?[^"|']{0,}|))              # ? mark with parameters
 
  )             
  
  (?:"|')[^\n]*)                    # End newline delimiter

""", re.VERBOSE)

# Parse command line
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input",
                    help="Input a: URL, file or folder. \
                    For folders a wildcard can be used (e.g. '/*.js').",
                    required="True", action="store")
parser.add_argument("-o", "--output",
                    help="Where to save the file, \
                    including file name. Default: output.html",
                    action="store", default="output.html")
parser.add_argument("-r", "--regex",
                    help="RegEx for filtering purposes \
                    against found endpoint (e.g. ^/api/)",
                    action="store")
args = parser.parse_args()

# Error messages


def parser_error(errmsg):
    print("Usage: python %s [Options] use -h for help" % sys.argv[0])
    print("Error: %s" % errmsg)
    sys.exit()

# Parse input


def parser_input(input):
    if input.startswith(('http://', 'https://',
                         'file://', 'ftp://', 'ftps://')):
        return [input]
    elif "*" in input:
        paths = glob.glob(os.path.abspath(input))
        for index, path in enumerate(paths):
            paths[index] = "file://%s" % path
        return (paths if len(paths) > 0 else parser_error('Input with wildcard does \
        not match any files.'))
    else:
        return ["file:///%s" % os.path.abspath(input)]

# Send request using Requests


def send_request(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept': 'text/html,\
        application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.8',
        'Accept-Encoding': 'gzip',
    }

    s = requests.Session()
    s.mount('file://', FileAdapter())
    content = s.get(url, headers=headers, timeout=1, stream=True)
    return content.text if hasattr(content, "text") else content.content

# Parse url


def parser_file(url):
    try:
        content = send_request(url)
    except Exception as e:
        parser_error("invalid input defined or SSL error: %s" % e)

    # Beautify
    content = jsbeautifier.beautify(content)

    # Match Regex + Delete duplicates
    items = re.findall(regex, content)
    #items = sorted(set(items))
    filtered_items = []

    for item in items:
        # Remove other capture groups from regex results
        group = list(filter(None, item))

        if args.regex:
            if re.search(args.regex, group[1]):
                filtered_items.append(group)
        else:
            filtered_items.append(group)

    return filtered_items

# Program
files = parser_input(args.input)

html = """
<style>.text {font-size:16px;margin:5px;font-family:Helvetica sans-serif;color:#323232;background-color:white;!important}\
.container {background-color:#e9e9e9;padding:5px;\
font-family:helvetica;font-size:13px;border-width: 1px;\
border-style:solid;border-color:#8a8a8a;\
color:#323232;margin-bottom:15px;}</style>
"""

for file in files:
    endpoints = parser_file(file)
    html += "<h1>%s</h1>" % cgi.escape(file)

    for endpoint in endpoints:
        string = "<div><p class='text'>%s" % cgi.escape(endpoint[1])
        string2 = "</p><div class='container'>%s</div></div>" % cgi.escape(
            endpoint[0]
        )
        string2 = string2.replace(
            cgi.escape(endpoint[1]),
            "<span style='background-color:yellow'>%s</span>" %
            cgi.escape(endpoint[1])
        )
        html += string + string2

try:    
    text_file = open(args.output, "wb")
    text_file.write(html.encode('utf-8'))
    text_file.close()
    print("URL to access output: file:///%s" % os.path.abspath(args.output))
except Exception as e:
    print("Output can't be saved in %s due to exception: %s" % (args.output, e))

