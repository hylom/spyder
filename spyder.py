# -*- coding: utf-8 -*-
"""spyder.py -- tiny and customizable WWW spider.

This module helps to fetch WWW contents. 

This module provides below classes and functions.

Spyder -- Spyder base class.
SpyderError -- Error class for exception process.
"""

__all__ = ["spyder"]
__version__ = "0.10"

import urllib
import HTMLParser
import os.path
import re
import sys
import urlparse
from string import Template

class SpyderError(Exception):
    """Spyder's exception handler class."""
    def __init__(self, name, value):
        self.value = value
        self.name = name

    def __str__(self):
        return self.name + ":" + repr(self.value)


class LinkParser(HTMLParser.HTMLParser):
    """Parse HTML and extract A tag's link url.

usage:
    url = "http://hogehoge.net/foo/bar.html"
    p = LinkParser()
    p.parse(html_string, url)
    anchors = p.get_anchors()
    imgs = p.get_imgs()
"""

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self._anchors = []
        self._imgs = []

    def parse(self, html_string, url):
        """Parse html_string with url, and return anchors"""
        self._anchors = []
        self._imgs = []
        self._links = []
        self._base_url_items = urlparse.urlparse(url)
        self.feed(html_string)

    def get_anchors(self):
        """return feed()'s result."""
        return self._anchors

    def get_imgs(self):
        """return feed()'s result."""
        return self._imgs

    def get_links(self):
        """return feed()'s result."""
        return self._links

    def handle_starttag(self, tag, attrs):
        """starttag handler."""

        """DEBUG CODE:
        if attrs:
            try:
                str = "-".join([x+":"+y for (x,y) in attrs])
            except TypeError:
                str = ""
            print >> sys.stderr, "<%s> %s" % (tag, str)
        else:
            print >> sys.stderr, "<%s>" % (tag,)
        """

        if tag == "a":
            for (attr, val) in attrs:
                if attr == "href":
                    self._anchors.append(self._regularize_url(val))
                    break
        if tag == "img":
            for (attr, val) in attrs:
                if attr == "src":
                    self._imgs.append(self._regularize_url(val))
                    break
        if tag == "link":
            for (attr, val) in attrs:
                if attr == "href":
                    self._links.append(self._regularize_url(val))
                    break

    def _regularize_url(self, url):
        """regularize given url."""
        # urlparse.urlparse("http://hoge.net/foo/var/index.html;q?a=b#c")
        #
        #       0       1           2                      3    4      5      
        #  -> ('http', 'hoge.net', '/foo/var/index.html', 'q', 'a=b', 'c')
        #
        current_term = self._base_url_items
        current_dir = os.path.dirname(current_term[2])
        current_last = os.path.basename(current_term[2])

        result = urlparse.urlparse(url)
        term = list(result)
        
        if not term[0]:
            term[0] = current_term[0] + "://"
        else:
            term[0] = term[0] + "://"
        if not term[1]:
            term[1] = current_term[1]
        if term[2] and term[2][0] != "/":
            term[2] = os.path.normpath(current_dir + "/" + term[2])
        if term[3]:
            term[3] = ";" + term[3]
        if term[4]:
            term[4] = "?" + term[4]
        if term[5]:
            term[5] = "#" + term[5]

        url = "".join(term)
        return url


class AnchorParser(LinkParser):
    """Parse HTML and extract A tag's link url.

usage:
    url = "http://hogehoge.net/foo/bar.html"
    p = AnchorParser()
    p.parse(html_string, url)
    anchors = p.get_anchors()
    imgs = p.get_imgs()
"""
    pass


def regularize_url(parsed_baseurl, url):
    """regularize given url.
    usage:
    parsed_baseurl = urlparse.urlparse(baseurl)
    url = "http://hoge.net/foo/var/index.html;q?a=b#c"
    re_url = regularized_url(parsed_baseurl, url)
    """
    # urlparse.urlparse("http://hoge.net/foo/var/index.html;q?a=b#c")
    #
    #       0       1           2                      3    4      5      
    #  -> ('http', 'hoge.net', '/foo/var/index.html', 'q', 'a=b', 'c')
    #
    current_term = parsed_baseurl
    current_dir = os.path.dirname(current_term[2])
    current_last = os.path.basename(current_term[2])

    result = urlparse.urlparse(url)
    term = list(result)

    if not term[0]:
        term[0] = current_term[0] + "://"
    else:
        term[0] = term[0] + "://"
    if not term[1]:
        term[1] = current_term[1]
    if term[2] and term[2][0] != "/":
        term[2] = os.path.normpath(current_dir + "/" + term[2])
    if term[3]:
        term[3] = ";" + term[3]
    if term[4]:
        term[4] = "?" + term[4]
    if term[5]:
        term[5] = "#" + term[5]

    url = "".join(term)
    return url


class CSSParser(object):
    """Parse CSS file to extract urls from url() and src='' element.

usage:
    url = "http://hogehoge.net/foo/bar.css"
    p = CSSParser()
    p.parse(css_string, url)
    refs = p.get_refs()
"""
    def __init__(self):
        self._refs = []

    def _exp_refactor(self, exps):
        flag = False
        while not flag:
            for comp in exps:
                s = exps[comp]
                if s.find("${") != -1:
                    t = Template(s)
                    exps[comp] = t.safe_substitute(exps)
                    break
            else:
                flag = True

    def parse(self, html_string, url):
        """Parse html_string with url"""
        self._refs = []
        self._parsed_baseurl = urlparse.urlparse(url)

        exps = dict(unicode=r"""\\[0-9a-f]{1,6}[ \n\r\t\f]?""",
                    w=r"""[ \t\r\n\f]*""",
                    nl=r"""\n|\r\n|\r|\f""",
                    nonascii=r"""[^\0-\177]""",
                    escape=r"""${unicode}|\\[^\n\r\f0-9a-f]""",
                    string1=r'''\"((:?[^\n\r\f\\"]|\\${nl}|${escape})*)\"''',
                    string2=r"""\'((:?[^\n\r\f\\']|\\${nl}|${escape})*)\'""",
                    string=r"""${string1}|${string2}""",
                    uri=r"""url\(${w}${string1}${w}\)|url\(${w}${string2}${w}\)|url\(${w}((:?[!#$%&*-~]|${nonascii}|${escape})*)${w}\)""",
                    )

        self._exp_refactor(exps)
        #print exps["uri"]
        rex_uri = re.compile(exps["uri"])
        for m in rex_uri.finditer(html_string, re.S|re.U):
            uri = filter(None, m.groups())[0]
            #print ">", filter(None, m.groups())[0]
            self._refs.append(self._regularize_url(uri))

    def _regularize_url(self, url):
        return regularize_url(self._parsed_baseurl, url)
        
        
    def get_refs(self):
        """return result of parsing."""
        return self._refs
    


class _DownloadQueue(object):
    """Inner class"""

    def __init__(self):
        """constructor."""
        self.init()

    def init(self):
        """clear queue"""
        self.queue = []
        self.map = {}

    def append(self, url):
        """append url to queue"""
        if not self.map.has_key(url):
            self.map[url] = 1
            self.queue.append(url)

    def pop(self):
        """get queue's 1st item."""
        url = self.queue.pop()
        self.map[url] = 0
        return url


class Spyder(object):
    """WWW Spider base class."""
    version = __version__

    def __init__(self):
        """Constructor"""
        self.queue = _DownloadQueue()
        self._current_url = ""
        self._last_parser = None
        self._last_parsed_url = ""

    def current_url(self):
        """get current proccessing url."""
        return self._current_url

    def append_url(self, url):
        """append url to fetch."""
        self.queue.append(url)

    def handle_url(self, url):
        """check url should be traced or not. if trace, return True. Normally, you should override this function."""
        return False

    def handle_start_fetch(self, url):
        """this function is called when start to fetch url."""
        pass

    def handle_data(self, url, level, data):
        """this function is called when data grabbed."""
        pass

    def run(self):
        """Run grubbber"""
        try:
            url = self.queue.pop()
        except IndexError:
            url = None
        while(url):
            # get html from url
            self.handle_start_fetch(url)
            html = self.grab_by_get(url)
            self._current_url = url
            self.handle_data(url, 0, html)

            # extract links from html
            anchors = self.extract_anchors(html, url)
            for anchor in anchors:
                (s, frag) = urlparse.urldefrag(anchor)
                if self.handle_url(s):
                    self.queue.append(s)

            # next
            try:
                url = self.queue.pop()
            except IndexError:
                url = None

    def grab_by_get(self, url):
        """grab given url's content  by GET method"""
        u = urllib.urlopen(url)
        data = u.read()
        return data

    def grab_by_post(self, url, params):
        """grab given url's content  by POST method"""
        encoded_params = urllib.urlencode(params)
        u = urllib.urlopen(url, encoded_params)
        data = u.read()
        return data

    def extract_anchors(self, html, url):
        """extract link anchors from HTML"""
        p = self.parse(html, url)
        return p.get_anchors()

    def extract_imgs(self, html, url):
        """extract img srcs from HTML"""
        p = self.parse(html, url)
        return p.get_imgs()

    def regularize_html(self, html):
        """remove or convert some illegal tags, texts, etc. for parse"""
        # remove script tag
        rex = re.compile(r"<\s*script[^>]*?>.*?</script>", re.S)
        rex2 = re.compile(r"<\s*noscript[^>]*?>.*?</noscript>", re.S)
        tmp = rex.sub("", html)
        html = rex2.sub("", tmp)

        # remove some invalid element
        # example: <! -- this is comment. -->
        rex = re.compile(r"<!\s.*?>", re.S)
        html = rex.sub("", html)
        return html

    def parse(self, html, url):
        """parsse from HTML"""
        if url == self._last_parsed_url and self._last_parser:
            p = self._last_parser
        else:
            html_r = self.regularize_html(html)
            p = AnchorParser()
            p.parse(html_r, url)
            self._last_parsed_url = url
            self._last_parser = p
        return p

