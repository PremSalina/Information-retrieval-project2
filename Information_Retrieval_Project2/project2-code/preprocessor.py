import re
from nltk.stem import PorterStemmer
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords', quiet=True)

class Preprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.ps = PorterStemmer()

    def get_doc_id(self, doc):
        arr = doc.split("\t")
        return int(arr[0]), arr[1]

    def tokenizer(self, text):
        text = text.lower()
        text = re.sub(r"[^a-zA-Z0-9 ]", " ", text)
        text = text.strip() 
        text = re.sub(' +', ' ', text)
        tokens = text.split()
        tokens = [word for word in tokens if word not in stopwords.words('english')]
        terms = [w.replace(w, self.ps.stem(w)) for w in tokens]
        return terms
