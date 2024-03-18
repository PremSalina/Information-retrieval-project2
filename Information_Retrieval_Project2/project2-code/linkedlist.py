import math
from collections import OrderedDict

class Node:
    def __init__(self, value=None, next=None, skip=None):
        self.value = value
        self.next = next
        self.skip = skip

class LinkedList:
    def __init__(self):
        self.start_node = None
        self.end_node = None
        self.length, self.n_skips, self.idf = 0, 0, 0.0
        self.skip_length = None

    def traverse_list(self):
        traversal = []
        if self.start_node is None:
            return
        else:
            current = self.start_node
            while current:
                doc_id = current.value['doc_id']
                traversal.append(doc_id)
                current = current.next
            return traversal

    def traverse_skips(self):
        traversal = []
        if self.start_node is None:
            return
        else:
            current = self.start_node
            while current.skip:
                doc_id = current.value['doc_id']
                traversal.append(doc_id)
                current = current.skip
            traversal.append(current.value['doc_id'])
            return traversal

    def add_skip_connections_list(self, length_of_postings_list):
        n_skips = int(math.sqrt(length_of_postings_list))
        if n_skips * n_skips == length_of_postings_list:
            n_skips -= 1
        length_between_skips = int(round(math.sqrt(length_of_postings_list), 0))

        temp = self.start_node
        current = self.start_node

        for i in range(n_skips):
            for j in range(length_between_skips - 1):
                if current:
                    current = current.next

            if current and temp:
                temp.skip = current.next
                temp = temp.skip
                current = temp


    def insert_at_end(self, value):
        new_node = Node(value)

        if self.start_node is None or value['doc_id'] < self.start_node.value['doc_id']:
            new_node.next = self.start_node
            self.start_node = new_node
        else:
            current = self.start_node

            while current.next and value['doc_id'] > current.next.value['doc_id']:
                current = current.next

            if not current.next or current.next.value['doc_id'] != value['doc_id']:
                new_node.next = current.next
                current.next = new_node


    def tf_idf_sort(self):
        if self.start_node is None:
            return []

        sorted_doc_id_tf_tuples = []

        current = self.start_node
        while current:
            doc_id = current.value['doc_id']
            tf_idf = current.value['tf']
            sorted_doc_id_tf_tuples.append((doc_id, tf_idf))
            current = current.next

        sorted_doc_id_tf_tuples.sort(key=lambda x: x[1], reverse=True)

        sorted_doc_ids = [doc_id for doc_id, _ in sorted_doc_id_tf_tuples]

        return sorted_doc_ids



    def get_length_of_posting_list(self):
        current = self.start_node
        count = 0

        while current:
            count += 1
            current = current.next

        return count

    def set_tfidf(self, term_idf):
        current = self.start_node

        while current:
            current.value['tf'] *= term_idf
            current = current.next


    def remove_duplicates(self):
        current = self.start_node

        while current and current.next:
            if current.value == current.next.value:
                current.next = current.next.next
            else:
                current = current.next

    
    def count(self):
        current = self.start_node
        count = 0
        while current:
            count += 1
            current = current.next
        return count
    
    def intersection(self, postings_list1, postings_list2, skip_indicator):
        merged_list = LinkedList()
        list1 = postings_list1
        list2 = postings_list2
        comparisons = 0

        p1 = list1.start_node
        p2 = list2.start_node

        while p1 and p2:
            doc_id1 = p1.value['doc_id']
            doc_id2 = p2.value['doc_id']

            if doc_id1 == doc_id2:
                merged_list.insert_at_end(p1.value)
                p1 = p1.next
                p2 = p2.next
            elif doc_id1 < doc_id2:
                if skip_indicator and p1.skip and p1.skip.value['doc_id'] < doc_id2:
                    p1 = p1.skip
                else:
                    p1 = p1.next
            else:
                if skip_indicator and p2.skip and p2.skip.value['doc_id'] < doc_id1:
                    p2 = p2.skip
                else:
                    p2 = p2.next

            comparisons += 1

        return merged_list, comparisons
