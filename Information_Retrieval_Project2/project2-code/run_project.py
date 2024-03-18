import copy

from tqdm import tqdm
from preprocessor import Preprocessor
from indexer import Indexer
from collections import OrderedDict
from linkedlist import LinkedList
import inspect as inspector
import sys
import argparse
import json
import time
import random
import flask
from flask import Flask
from flask import request
import hashlib

app = Flask(__name__)


class ProjectRunner:
    def __init__(self):
        self.preprocessor = Preprocessor()
        self.indexer = Indexer()
        self.number_of_documents = 0
        self.start_node = None

    def intersection(self, postings_list1, postings_list2, skip_indicator):
        merged_list = LinkedList()
        p1 = postings_list1.start_node
        p2 = postings_list2.start_node
        comparisons = 0

        while p1 and p2:
            doc_id1 = p1.value['doc_id']
            doc_id2 = p2.value['doc_id']

            if doc_id1 == doc_id2:
                merged_list.insert_at_end(p1.value)
                p1 = p1.next
                p2 = p2.next
            elif doc_id1 < doc_id2:
                p1 = p1.next
            else:
                p2 = p2.next

            comparisons += 1

        return merged_list, comparisons

    def _merge(self, sorted_terms_list, skip_indicator, tf_idf_sort):
        if len(sorted_terms_list) == 1:
            term = sorted_terms_list[0][0]
            merged_list = self.indexer.inverted_index[term]
        else:
            merged_list = None
        total_comparisons = 0

        for i in range(1, len(sorted_terms_list)):
            term_i_1 = sorted_terms_list[i - 1][0]
            term_i = sorted_terms_list[i][0]

            term_i_1_postings = self.indexer.inverted_index[term_i_1]
            term_i_postings = self.indexer.inverted_index[term_i]

            if merged_list:
                list_after_merge, comparisons = self.intersection(merged_list, term_i_postings, skip_indicator)
            else:
                list_after_merge, comparisons = self.intersection(term_i_1_postings, term_i_postings, skip_indicator)

            merged_list = list_after_merge
            total_comparisons += comparisons

        if not tf_idf_sort:
            merged_list = merged_list.traverse_list()
        else:
            merged_list = merged_list.tf_idf_sort()

        return merged_list, total_comparisons




    def _daat_and(self, input_term_arr, skip_indicator, tf_idf_sort):
        sorted_terms_list = OrderedDict({})
        term_dict = {}

        for term in input_term_arr:
            if term not in self.indexer.inverted_index:
                return [], 0
            posting_list = self.indexer.inverted_index[term]
            term_dict[term] = posting_list.get_length_of_posting_list()

        sorted_terms_list = sorted(term_dict.items(), key=lambda x: x[1])

        if not sorted_terms_list:
            return [], 0

        merged_list, total_comparisons = self._merge(sorted_terms_list, skip_indicator, tf_idf_sort)

        return merged_list, total_comparisons


    def _get_postings(self, term):
        posting_list = self.indexer.inverted_index.get(term, None)
        
        if posting_list:
            list_of_doc_id = posting_list.traverse_list()
            list_of_doc_id_with_skip = posting_list.traverse_skips()
            return list_of_doc_id, list_of_doc_id_with_skip
        else:
            return [], []


    def _output_formatter(self, op):
        if op is None or len(op) == 0:
            return [], 0
        op_no_score = [int(i) for i in op]
        results_cnt = len(op_no_score)
        return op_no_score, results_cnt


    def run_indexer(self, corpus):
        with open(corpus, 'r', encoding="utf8") as fp:
            for line in tqdm(fp.readlines()):
                self.number_of_documents = +1
                doc_id, document = self.preprocessor.get_doc_id(line)
                tokenized_document = self.preprocessor.tokenizer(document)
                self.indexer.generate_inverted_index(doc_id, tokenized_document)
        self.indexer.sort_terms()
        self.indexer.add_skip_connections()
        self.indexer.calculate_tf_idf(self.number_of_documents)

    def get_number_of_documents(self):
        return self.number_of_documents

    def sanity_checker(self, command):
        index = self.indexer.get_index()
        kw = random.choice(list(index.keys()))
        return {"index_type": str(type(index)),
                "indexer_type": str(type(self.indexer)),
                "post_mem": str(index[kw]),
                "post_type": str(type(index[kw])),
                "node_mem": str(index[kw].start_node),
                "node_type": str(type(index[kw].start_node)),
                "node_value": str(index[kw].start_node.value),
                "command_result": eval(command) if "." in command else ""}

    def run_queries(self, query_list):
        output_dict = {'postingsList': {},
                       'postingsListSkip': {},
                       'daatAnd': {},
                       'daatAndSkip': {},
                       'daatAndTfIdf': {},
                       'daatAndSkipTfIdf': {},
                       }

        for query in tqdm(query_list):
            input_term_arr = []  # Tokenized query. To be implemented.
            print("query: ", query)
            input_term_arr = self.preprocessor.tokenizer(query)
            print("input__term_arr: ",input_term_arr)
            for term in input_term_arr:
                postings, skip_postings = None, None

                print("term: ", term)
                postings, skip_postings = self._get_postings(term)

                output_dict['postingsList'][term] = postings
                output_dict['postingsListSkip'][term] = skip_postings

            and_op_no_skip, and_op_skip, and_op_no_skip_sorted, and_op_skip_sorted = None, None, None, None
            and_comparisons_no_skip, and_comparisons_skip, \
                and_comparisons_no_skip_sorted, and_comparisons_skip_sorted = None, None, None, None

            and_op_no_skip, and_comparisons_no_skip = self._daat_and(input_term_arr, False, False)
            and_op_skip, and_comparisons_skip = self._daat_and(input_term_arr, True, False)
            and_op_no_skip_sorted, and_comparisons_no_skip_sorted = self._daat_and(input_term_arr, False, True)
            and_op_skip_sorted, and_comparisons_skip_sorted = self._daat_and(input_term_arr, True, True)

            and_op_no_score_no_skip, and_results_cnt_no_skip = self._output_formatter(and_op_no_skip)
            and_op_no_score_skip, and_results_cnt_skip = self._output_formatter(and_op_skip)
            and_op_no_score_no_skip_sorted, and_results_cnt_no_skip_sorted = self._output_formatter(and_op_no_skip_sorted)
            and_op_no_score_skip_sorted, and_results_cnt_skip_sorted = self._output_formatter(and_op_skip_sorted)

            output_dict['daatAnd'][query.strip()] = {}
            output_dict['daatAnd'][query.strip()]['results'] = and_op_no_score_no_skip
            output_dict['daatAnd'][query.strip()]['num_docs'] = and_results_cnt_no_skip
            output_dict['daatAnd'][query.strip()]['num_comparisons'] = and_comparisons_no_skip

            output_dict['daatAndSkip'][query.strip()] = {}
            output_dict['daatAndSkip'][query.strip()]['results'] = and_op_no_score_skip
            output_dict['daatAndSkip'][query.strip()]['num_docs'] = and_results_cnt_skip
            output_dict['daatAndSkip'][query.strip()]['num_comparisons'] = and_comparisons_skip

            output_dict['daatAndTfIdf'][query.strip()] = {}
            output_dict['daatAndTfIdf'][query.strip()]['results'] = and_op_no_score_no_skip_sorted
            output_dict['daatAndTfIdf'][query.strip()]['num_docs'] = and_results_cnt_no_skip_sorted
            output_dict['daatAndTfIdf'][query.strip()]['num_comparisons'] = and_comparisons_no_skip_sorted

            output_dict['daatAndSkipTfIdf'][query.strip()] = {}
            output_dict['daatAndSkipTfIdf'][query.strip()]['results'] = and_op_no_score_skip_sorted
            output_dict['daatAndSkipTfIdf'][query.strip()]['num_docs'] = and_results_cnt_skip_sorted
            output_dict['daatAndSkipTfIdf'][query.strip()]['num_comparisons'] = and_comparisons_skip_sorted

        return output_dict


@app.route("/execute_query", methods=['POST'])
def execute_query():
    start_time = time.time()

    queries = request.json["queries"]
    #random_command = request.json["random_command"]

    """ Running the queries against the pre-loaded index. """
    #output_dict = runner.run_queries(queries, random_command)

    output_dict = runner.run_queries(queries)


    """ Dumping the results to a JSON file. """
    with open(output_location, 'w') as fp:
        json.dump(output_dict, fp)

    response = {
        "Response": output_dict,
        "time_taken": str(time.time() - start_time),
        "username_hash": username_hash
    }
    return flask.jsonify(response)

if __name__ == "__main__":
    """ Driver code for the project, which defines the global variables.
        Do NOT change it."""

    output_location = "project2_output.json"
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--corpus", type=str, help="Corpus File name, with path.", default='input_corpus.txt')
    parser.add_argument("--output_location", type=str, help="Output file name.", default=output_location)
    parser.add_argument("--username", type=str,
                        help="Your UB username. It's the part of your UB email id before the @buffalo.edu. "
                             "DO NOT pass incorrect value here", default='swetasri')

    argv = parser.parse_args()

    corpus = argv.corpus
    output_location = argv.output_location
    username_hash = hashlib.md5(argv.username.encode()).hexdigest()

    """ Initialize the project runner"""
    runner = ProjectRunner()

    """ Index the documents from beforehand. When the API endpoint is hit, queries are run against 
        this pre-loaded in memory index. """
    runner.run_indexer(corpus)

    app.run(host="0.0.0.0", port=9999)
