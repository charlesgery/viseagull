from pandas import DataFrame
from sklearn.neighbors import DistanceMetric

from .Analyzer import Analyzer

class LogicalAnalyzer(Analyzer):

    def __init__(self, url) -> None:
        super().__init__(url)

        self.couplings_type = 'logical'

    def compute_couplings(self):
        
        self.run_general_analysis(
            get_logical_couplings_df=True,
            get_commit_to_files=True,
            get_dates=True
            )


    def get_distance_matrix(self):
        """ Computes a distance matrix using the jaccard distance on the inputed dataframe.
        """

        dist = DistanceMetric.get_metric('jaccard')
        distance_matrix = dist.pairwise(self.df.iloc[:,:].to_numpy())

        distance_df = DataFrame(distance_matrix, index=self.df.index, columns=self.df.index)

        self.distance_matrix = distance_df

        return distance_df