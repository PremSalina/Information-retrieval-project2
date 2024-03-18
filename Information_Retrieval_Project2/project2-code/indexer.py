from collections import OrderedDict
from linkedlist import LinkedList

class Indexer:
    def __init__(self):
        self.inverted_index = OrderedDict()
        self.linkedlist = LinkedList()

    def get_index(self):
        return self.inverted_index

    def generate_inverted_index(self, doc_id, tokenized_document):
        tf_dict = {}
        total_terms_in_doc = len(tokenized_document)

        for term in tokenized_document:
            tf_dict[term] = tf_dict.get(term, 0) + 1

        for term in tf_dict:
            tf_dict[term] = tf_dict[term] / total_terms_in_doc

        for term in tokenized_document:
            self.add_to_index(term, doc_id, tf_dict[term])


    def add_to_index(self, term, doc_id, tf):
        if term in self.inverted_index:
            postings_list = self.inverted_index[term]
        else:
            postings_list = LinkedList()
            self.inverted_index[term] = postings_list

        doc_id_tf = {'doc_id': doc_id, 'tf': tf}
        postings_list.insert_at_end(doc_id_tf)


    def sort_terms(self):
        sorted_index = OrderedDict()
        for k in sorted(self.inverted_index.keys()):
            sorted_index[k] = self.inverted_index[k]
        self.inverted_index = sorted_index

    def add_skip_connections(self):
        for term, postings_list in self.inverted_index.items():
            length_of_postings_list = postings_list.get_length_of_posting_list()
            postings_list.add_skip_connections_list(length_of_postings_list)
            postings_list.remove_duplicates()


    def calculate_tf_idf(self, total_documents):
        total_documents_count = total_documents

        for term, postings_list in self.inverted_index.items():
            length_of_postings_list = postings_list.get_length_of_posting_list()
            term_idf = total_documents_count / length_of_postings_list
            postings_list.set_tfidf(term_idf)
