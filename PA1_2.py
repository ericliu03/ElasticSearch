__author__ = 'EricLiu'

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from PA1_1 import WikiNovelExtractor


class NovelES:
    def __init__(self, docs):
        self.es = Elasticsearch()
        self.docs = docs
        self.index = 'i_novels'
        self.type = 'novel'

    def set_up_es(self):
        setting = {
            "index": {
                "number_of_replicas": 0,
                "number_of_shards": 3
            },
            "analysis": {
                "filter": {
                    "stemmer_eng": {
                        "type": "stemmer",
                        "name": "light_english"
                    }
                },
                "analyzer": {
                    "analyzer_eng": {
                        "type": "custom",
                        "tokenizer": "whitespace",
                        "filter": ["lowercase", "stemmer_eng"]
                    }
                }
            }
        }
        mapping = {
            "novel": {
                "properties": {
                    "title": {"type": "string",
                              "index": "not_analyzed"},
                    "authors": {"type": "string",
                                "index": "not_analyzed"},
                    "category": {"type": "string",
                                 "index": "not_analyzed"},
                    "year": {"type": "integer",
                             "index": "not_analyzed"},
                    "text": {"type": "string",
                             "analyzer": "analyzer_eng"},
                }
            }
        }
        try:
            self.es.indices.create(index="i_novels", body=setting)
            self.es.indices.put_mapping(index=self.index, doc_type=self.type, body=mapping)
            self.bulk_create()
        except Exception, e:
            print "ERROR: Index exists. Skip bulkload"
            pass

    def bulk_create(self):
        actions = []
        for body in self.docs:
            actions.append({
                '_index': self.index,
                '_type': self.type,
                '_source': body
            })
        helpers.bulk(self.es, actions)

    def q_range(self, q1, q2):
        temp = {
            "query": {
                "match_all": {}
            },
            "facets": {
                "range1": {
                    "range": {
                        "field": "year",
                        "ranges": [
                            {"from": q1, "to": q2}
                        ]
                    }
                }
            }
        }
        result = self.es.search(index=self.index, doc_type=self.type, body=temp)
        result = result['facets']['range1']['ranges'][0]
        print "From: ", result['from'], " To: ", result['to'], " Total Count: ", result['total_count']
        return result

    def q_total(self):
        temp = {
            "facets": {
                "total": {
                    "query": {
                        "match_all": {}
                    }
                }
            }
        }
        result = self.es.search(index=self.index, doc_type=self.type, body=temp)
        result = result['facets']['total']['count']
        print "Total Index Count: ", result
        return result

    def q_field(self, field_name='authors'):
        temp = {
            "facets": {
                "count": {
                    "terms": {
                        "field": field_name,
                        "size": 10000
                    }
                }
            }
        }
        result = self.es.search(index=self.index, doc_type=self.type, body=temp)
        result = result['facets']['count']['terms']
        print "Total %s Count: " % field_name, len(result)
        return result

    def test_queries(self):
        for i in range(0, 4):
            es_obj.q_range(1900+i*25, 1925+i*25)
        self.q_total()
        self.q_field('authors')
        self.q_field('category')

if __name__ == "__main__":
    wiki_obj = WikiNovelExtractor()
    pages = wiki_obj.load_json("wiki_all.txt")
    es_obj = NovelES(pages)
    es_obj.set_up_es()
    es_obj.test_queries()
    # print "Input your query in this format: field value"
    # print "Input exit() to exit"
    # while True:
    #     input = raw_input("Your query: ")
    #     if input == 'exit()':
    #         break
    #     input = input.split(' ')
    #     res = es_obj.es_query(input[0], input[1])
    #     print res['facets']['range1']['ranges']