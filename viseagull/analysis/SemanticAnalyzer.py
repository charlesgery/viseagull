from ast import parse, walk, FunctionDef, ClassDef, Name
from re import findall

from math import log, sqrt

from pandas import DataFrame
from nltk.stem import PorterStemmer
from sklearn.metrics.pairwise import cosine_similarity

from .Analyzer import Analyzer

class SemanticAnalyzer(Analyzer):

    def __init__(self, url) -> None:
        super().__init__(url)

        self.couplings_type = 'semantic'

        self.tf_idf_df = None
        self.file_to_identifiers = None

    def compute_couplings(self):
        
        self.file_to_identifiers = self.get_corpus()

        self.preprocess_words(self.file_to_identifiers)

        voc_size, voc_to_index = self.compute_voc(self.file_to_identifiers)

        tf = self.compute_tf(voc_to_index, self.file_to_identifiers)
        idf = self.compute_idf(voc_to_index, self.file_to_identifiers)
        tf_idf = self.compute_tf_idf(voc_to_index, tf, idf)


        self.tf_idf_df = DataFrame.from_dict(tf_idf, orient='index')

        self.run_general_analysis(
            get_logical_couplings_df=True,
            get_commit_to_files=True,
            get_dates=True
            )

        

    def get_distance_matrix(self):
        
        distance_matrix = cosine_similarity(self.tf_idf_df)
        for i in range(len(distance_matrix)):
            distance_matrix[i][i] = 1
        distance_df = DataFrame(distance_matrix, index=self.tf_idf_df.index, columns=self.tf_idf_df.index)

        self.distance_matrix = distance_df

        return distance_df
    
    def get_corpus(self):
        """ Get a list of identifiers of each file in a repo.
        """

        file_to_identifiers = {}
        for file_path in self.repo_files_path:


            try :
                with open(self.repo_folder + '\\' + file_path) as data_source:
                    ast_root = parse(data_source.read())
                    
                identifiers = []

                for node in walk(ast_root):
                    if isinstance(node, Name):
                        identifiers.append(node.id)
                    elif isinstance(node, FunctionDef) or isinstance(node, ClassDef):
                        identifiers.append(node.name)

                file_to_identifiers[file_path] = identifiers

            except:
                pass
        
        return file_to_identifiers

    def preprocess_words(self, file_to_identifiers):
        """ Preprocess words for further analysis : stems, split and lower words.
        """

        stemmer = PorterStemmer()

        for key in file_to_identifiers.keys():

            old_words = file_to_identifiers[key]
            new_words = []

            for i in range(len(old_words)):

                splitted_sentence = self.split_sentence(old_words[i])
                for word in splitted_sentence:
                    new_words.append(word)


            new_words = [str.lower(word) for word in new_words]
            new_words = [stemmer.stem(word) for word in new_words]

            file_to_identifiers[key] = new_words

    @staticmethod
    def split_sentence(word):
        """ Split a snake or camel case string into its composing words.
        """

        # Snake split
        splitted_snake_sentence = word.split('_')

        # camel_word = re.sub(r'_(.)', lambda m: m.group(1).upper(), word)

        splitted_sentence = []
        for snake_word in splitted_snake_sentence:
            camel_words = findall(r'.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', snake_word)
            for camel_word in camel_words:
                splitted_sentence.append(camel_word)

        return splitted_sentence

    @staticmethod
    def compute_voc(file_to_identifiers):
        """ Compute the vocabulary of a repo (list of all the words).
        """

        voc = set()

        for _, value in file_to_identifiers.items():

            for word in value:

                if word not in voc:
                    voc.add(word)

        voc_size = len(voc)

        voc_to_index = {}

        i = 0
        for word in voc:
            voc_to_index[word] = i
            i += 1

        return voc_size, voc_to_index

    @staticmethod
    def compute_tf(voc_to_index, file_to_identifiers):
        """ Compute the tf values for each file in repo.
        """

        tf = {}

        for file_path in file_to_identifiers.keys():

            tf[file_path] = [0 for _ in range(len(voc_to_index))]

            for word in file_to_identifiers[file_path]:

                tf[file_path][voc_to_index[word]] += 1

            num_identifiers = len(file_to_identifiers[file_path])

            if num_identifiers > 0:
                tf[file_path] = [value / num_identifiers for value in tf[file_path]]

        return tf

    @staticmethod
    def compute_idf(voc_to_index, file_identifiers):
        """ Compute the idf values for each file in repo.
        """

        idf = {}

        for word in voc_to_index.keys():

            num_doc = 0

            for identifiers in file_identifiers.values():

                if word in identifiers:
                    num_doc += 1

            idf[word] = log(len(file_identifiers) / num_doc)

        return idf

    @staticmethod
    def compute_tf_idf(voc_to_index, tf, idf):
        """ Compute the tf_idf values for each file in repo.
        """

        tf_idf = {}

        for file_path in tf.keys():

            tf_idf[file_path] = [0 for _ in range(len(voc_to_index))]

            for word, index in voc_to_index.items():

                tf_idf[file_path][index] = tf[file_path][index] * idf[word]

        return tf_idf

    @staticmethod
    def compute_cosine_distance(a, b):
        """ Compute the cosine distance between two vectors a and b.
        """


        norm_a = 0
        norm_b = 0

        dot = 0

        for i in range(len(a)):

            dot += a[i] * b[i]

            norm_a += a[i] ** 2
            norm_b += b[i] ** 2

        norm_a = sqrt(norm_a)
        norm_b = sqrt(norm_b)

        return dot / (norm_a * norm_b)