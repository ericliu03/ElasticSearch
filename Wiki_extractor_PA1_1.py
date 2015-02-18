# course: COSI 132A
# date: 02/14/2015
# name: Yang Liu
# description: this file is used for extract information from wikipedia.
# By using wikitools and other method implemented here, this program is
# able to get information from wiki's infobox and text, including authors,
# categories, published year and whole page text.

__author__ = 'Yang_Liu'
from wikitools import wiki
from wikitools import category
from collections import Counter
import nltk
import string
import re
import json


class WikiNovelExtractor:
    """extract info from wiki"""
    def __init__(self, file_name='wiki_novel.txt'):
        self.file_name = file_name
        # author names and their times of appearances
        self.author_c = Counter()
        # categories and their times of appearances
        self.category_c = Counter()
        # times of appearances of 4 quarter of a century
        self.year_c = Counter()
        # total number of pages extracted
        self.page_id = 0
        self.pages = {}

    @staticmethod
    def inside_split(sen):
        """split words in a square bracket, and get the displayed one"""
        sen = sen.strip().strip('[').strip(']')
        if '|' in sen:
            return sen.split('|')[1]
        else:
            return sen

    @staticmethod
    def outside_split(sen):
        """split words outside a square bracket, mainly used for split different author names"""
        pattern = re.compile(r'<br>|, with|&<br />|and|,|&|,<br />')
        str_list = pattern.split(sen)
        str_list = [sen.strip('[').strip(']') for sen in str_list if sen.strip() != '']
        return str_list

    @staticmethod
    def get_title(text):
        """get the book's title from infobox"""
        book_pattern = r'name\s*\=\s*(?P<name>[^|]*)'
        match = re.search(book_pattern, text)
        title = ''
        if match:
            title = match.group('name').strip()
        return title

    def get_author(self, text):
        """get author name(s) from a infobox"""
        author_pattern = r'author\s*\=\s*(?P<name>[^=\n]*)[\n\|]'
        match = re.search(author_pattern, text)
        authors = []
        if match:
            names = match.group('name')
            names = self.outside_split(names)
            for name in names:
                authors.append(self.inside_split(name))
        else:
            authors = None
        return authors

    def get_year(self, text):
        """get publish year from a infobox"""
        year_pattern = r'date\s*\=.*(?P<year>(19|20)\d{2}).*[|\n]'
        match1 = re.search(year_pattern, text)
        if match1:
            year = self.inside_split(match1.group('year'))
        else:
            return None
        year = re.findall(r'\d{4}', year)
        if year:
            year = int(min(year))
        else:
            year = None
        return year

    @staticmethod
    def find_year(text):
        """find the publish year in text"""
        year_pattern = re.compile(r'(?P<year>(19|20)\d{2})')
        result = year_pattern.search(text)
        if result:
            return int(result.group('year'))
        else:
            return None

    @staticmethod
    def find_author(text):
        """find the author name in text"""
        # by using nltk tokenize, pos_tag to recognize 'PERSON' which is the name of author
        tokens = nltk.word_tokenize(filter(lambda x: x in string.printable, text))
        pos_tags = nltk.pos_tag(tokens)
        result = nltk.ne_chunk(pos_tags)
        for i in range(len(result)):
            author = ''
            if 'PERSON' in str(result[i]):
                for leaf in result[i].leaves():
                    author += leaf[0] + ' '
                author = author.strip()
                if author != u'Navbox':
                    return [author]

    @staticmethod
    def unhtml(html):
        """
        Remove HTML from the text.
        from: http://pastebin.com/idw8vQQK
        """
        html = re.sub(r'(?i)&nbsp;', ' ', html)
        html = re.sub(r'(?i)<br[ \\]*?>', '\n', html)
        html = re.sub(r'(?m)<!--.*?--\s*>', '', html)
        html = re.sub(r'(?i)<ref[^>]*>[^>]*</ ?ref>', '', html)
        html = re.sub(r'(?m)<.*?>', '', html)
        html = re.sub(r'(?i)&amp;', '&', html)
        return html

    @staticmethod
    def unwiki(wiki_text):
        """
        Remove wiki markup from the text.
        from: http://pastebin.com/idw8vQQK
        """
        wiki_text = re.sub(r'(?i)\{\{IPA(\-[^\|\{\}]+)*?\|([^\|\{\}]+)(\|[^\{\}]+)*?\}\}', lambda m: m.group(2), wiki_text)
        wiki_text = re.sub(r'(?i)\{\{Lang(\-[^\|\{\}]+)*?\|([^\|\{\}]+)(\|[^\{\}]+)*?\}\}', lambda m: m.group(2), wiki_text)
        wiki_text = re.sub(r'\{\{[^\{\}]+\}\}', '', wiki_text)
        wiki_text = re.sub(r'(?m)\{\{[^\{\}]+\}\}', '', wiki_text)
        wiki_text = re.sub(r'(?m)\{\|[^\{\}]*?\|\}', '', wiki_text)
        wiki_text = re.sub(r'(?i)\[\[Category:[^\[\]]*?\]\]', '', wiki_text)
        wiki_text = re.sub(r'(?i)\[\[Image:[^\[\]]*?\]\]', '', wiki_text)
        wiki_text = re.sub(r'(?i)\[\[File:[^\[\]]*?\]\]', '', wiki_text)
        wiki_text = re.sub(r'\[\[[^\[\]]*?\|([^\[\]]*?)\]\]', lambda m: m.group(1), wiki_text)
        wiki_text = re.sub(r'\[\[([^\[\]]+?)\]\]', lambda m: m.group(1), wiki_text)
        wiki_text = re.sub(r'\[\[([^\[\]]+?)\]\]', '', wiki_text)
        wiki_text = re.sub(r'(?i)File:[^\[\]]*?', '', wiki_text)
        wiki_text = re.sub(r'\[[^\[\]]*? ([^\[\]]*?)\]', lambda m: m.group(1), wiki_text)
        wiki_text = re.sub(r"''+", '', wiki_text)
        wiki_text = re.sub(r'(?m)^\*$', '', wiki_text)

        return wiki_text

    def clean_text(self, text):
        """clean the text: erasing brackets and references, also templates
        then lemmatize the text"""

        text = self.unhtml(text)
        text = self.unwiki(text)
        text = filter(lambda x: x in string.printable, text)
        return text

    def counter(self, book_dic):
        """count the numbers"""
        self.page_id += 1
        authors = book_dic['authors']
        if authors is not None:
            for author in authors:
                self.author_c[author] += 1

        for cat in book_dic['category']:
            self.category_c[cat] += 1

        year = int(book_dic['year']) if book_dic['year'] is not None else None
        if year is None:
            pass
        elif 1900 <= year < 1925:
            self.year_c['q1'] += 1
        elif year < 1950:
            self.year_c['q2'] += 1
        elif year < 1975:
            self.year_c['q3'] += 1
        elif year < 2000:
            self.year_c['q4'] += 1

    def get_page_info(self, page):
        """get information from each page"""
        book_dic = {'category': page.getCategories(),
                    'title': page.unprefixedtitle}

        text = page.getWikiText()

        # check if there is a infobox in this page
        infobox_pattern = r'\wnfobox \wook'
        if re.findall(infobox_pattern, text):
            book_dic['authors'] = self.get_author(text)
            book_dic['year'] = self.get_year(text)
            # last clean since we need infobox
            book_dic['text'] = self.clean_text(text)

        else:
            book_dic['text'] = self.clean_text(text)
            book_dic['year'] = self.find_year(book_dic['text'])
            book_dic['authors'] = self.find_author(book_dic['text'])

        self.counter(book_dic)
        return book_dic

    @staticmethod
    def to_jsonfile(pages, file_name):
        """transform dictionary to json in a file named file_name"""
        with open(file_name, 'w') as outfile:
            json.dump(pages, outfile, indent=4, sort_keys=True)

    def get_info_from_file(self):
        """load json from a file to python objective"""
        with open(self.file_name) as outfile:
            temp = json.load(outfile)
            return temp

    def get_info_from_wiki(self):
        """get information and store after extraction, return a list of dictionaries contains pages' info"""
        url = "http://en.wikipedia.org/w/api.php"
        cat = "20th-century_American_novels"
        wiki_obj = wiki.Wiki(url)
        wiki_cat = category.Category(wiki_obj, title=cat)
        wiki_pages = wiki_cat.getAllMembers()
        print 'Got pages, start extracting'
        total = len(wiki_pages)
        for page in wiki_pages:
            if self.page_id % 5 == 0:
                print "%.2f%%" % (100.0*self.page_id/total)
            self.pages[self.page_id] = self.get_page_info(page)
        print 'Extracting complete, write to file %s' % self.file_name
        self.to_jsonfile(self.pages, self.file_name)

        return self.pages

    def print_info(self):
        print 'number of books extracted: ', self.page_id
        print 'number of author: ', len(self.author_c)
        print 'number of category: ', len(self.category_c)
        print 'distribution of published year', self.year_c

if __name__ == "__main__":
    extractor = WikiNovelExtractor("wiki_all.txt")
    # extractor.get_info_from_wiki()
    dicts = extractor.get_info_from_file()
    for dic in dicts.itervalues():
        print dic
        extractor.counter(dic)
    extractor.print_info()



