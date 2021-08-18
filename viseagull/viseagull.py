import logging
from os import remove
import time

from argparse import ArgumentParser
from shutil import copy

from numpy import number

from viseagull.webserver import run_webserver
from viseagull.analysis.LogicalAnalyzer import LogicalAnalyzer
from viseagull.analysis.SemanticAnalyzer import SemanticAnalyzer

from viseagull.clustering.LogicalClusterer import LogicalClusterer
from viseagull.clustering.SemanticClusterer import SemanticClusterer

from viseagull.data_processing.DataProcessor import DataProcessor

def get_analyzer(couplings_type, url, remove_bulk):
    
    if couplings_type is not None:
        if couplings_type[0] == 'logical':
            analyzer = LogicalAnalyzer(url, remove_bulk)
        elif couplings_type[0] == 'semantic':
            analyzer = SemanticAnalyzer(url, remove_bulk)
        else:
            raise ValueError("Wrong couplings type")
    else:
        analyzer = LogicalAnalyzer(url, remove_bulk)

    return analyzer

def get_clusterer(couplings_type, distance_matrix):
    
    if couplings_type is not None:
        if couplings_type[0] == 'logical':
            clusterer = LogicalClusterer(distance_matrix)
        elif couplings_type[0] == 'semantic':
            clusterer = SemanticClusterer(distance_matrix)
        else:
            raise ValueError("Wrong couplings type")
    else:
        clusterer = LogicalClusterer(distance_matrix)

    return clusterer

def get_epsilon(number_files, number_commits, init_time):

    time_baseline = number_commits * 3.80640347e-02 + number_files * number_commits * 8.21324738e-06
    
    return init_time / time_baseline

def predict_execution_time(number_files, number_commits, epsilon, step):
    
    predicted_time = 0

    if step == 2:
        predicted_time = (number_files * 1.27241508e-04 + number_commits * 1.08355355e-04 +
            number_files * number_commits * 4.65037380e-07)
    elif step == 3:
        predicted_time = (number_files * number_commits * 4.52106394e-07 +
            (number_files ** 2) * number_commits * 1.32475623e-09 +
            number_files * (number_commits ** 2) * 1.05041833e-12)
    elif step == 4:
        predicted_time = (number_files * 3.33070576e-05 + (number_files ** 3) * 5.49653195e-12)
    elif step == 5:
        predicted_time = (number_files * 2.75483947e-03 +
            number_files * number_commits * 6.98932455e-06 +
            (number_files ** 2 * number_commits) * 9.12066810e-10)
    

    if predicted_time < 0:
        predicted_time = 0

    adjusted_predicted_time = epsilon * predicted_time

    return adjusted_predicted_time

def main():

    logging.basicConfig(level=logging.CRITICAL)

    logger = logging.getLogger('viseagull')
    logger.setLevel(level=logging.INFO)

    license = """A ludic visualization tool to explore your codebase. Copyright (C) 2021  Charles Géry
This program comes with ABSOLUTELY NO WARRANTY;'.
This is free software, and you are welcome to redistribute it
under certain conditions;\n\n"""
    logger.info(license)

    parser = ArgumentParser(description='Process repository url')
    parser.add_argument('url', type=str, nargs='?')
    parser.add_argument('--couplings', type=str, nargs=1, help="logical or semantic")
    parser.add_argument('--save', help='save template', action='store_true')
    parser.add_argument('--load', help='load existing template', type=str, nargs=1)
    parser.add_argument('--debug', help='displays running times', action='store_true')
    parser.add_argument('--remove-bulk', help="removes commits with more than N files from analysis", type=int, nargs=1)
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(level=logging.DEBUG)

    if args.url is None and args.load is None:
        parser.error("Viseagull requires the url to a repository. See --help for more details.")

    if args.load is not None:

        logger.info('Loading existing template')
        src = './saved_templates/' + args.load[0]
        dest = './visualization/data.js'
        copy(src, dest)

    else:

        logger.info('STEP 1/5 - Initializing analyzer')
        remove_bulk = -1
        if args.remove_bulk is not None:
            remove_bulk = args.remove_bulk[0]
        analyzer = get_analyzer(args.couplings, args.url, remove_bulk)
        
        number_files = analyzer.number_files
        number_commits = analyzer.total_commits
        init_time = analyzer.init_time
        epsilon = get_epsilon(number_files, number_commits, init_time)

        logger.info('STEP 2/5 - Analyzing Couplings')
        predicted_execution_time = predict_execution_time(number_files, number_commits, epsilon, 2)
        logger.debug(f'Predicted execution time : {predicted_execution_time}s')
        start_time = time.time()
        analyzer.compute_couplings()
        logger.debug(f'STEP 2/5 Executed in {time.time() - start_time}s\n')

        logger.info('STEP 3/5 - Computing distance matrix')
        predicted_execution_time = predict_execution_time(number_files, number_commits, epsilon, 3)
        logger.debug(f'Predicted execution time : {predicted_execution_time}s')
        start_time = time.time()
        distance_matrix = analyzer.get_distance_matrix()
        logger.debug(f'STEP 3/5 Executed in {time.time() - start_time}s\n')

        logger.info('STEP 4/5 - Computing Clustering')
        predicted_execution_time = predict_execution_time(number_files, number_commits, epsilon, 4)
        logger.debug(f'Predicted execution time : {predicted_execution_time}s')
        start_time = time.time()
        clusterer = get_clusterer(args.couplings, distance_matrix)
        clusterer.compute_clustering()
        logger.debug(f'STEP 4/5 Executed in {time.time() - start_time}s\n')

        logger.info('STEP 5/5 - Setting up visualization data')
        predicted_execution_time = predict_execution_time(number_files, number_commits, epsilon, 5)
        logger.debug(f'Predicted execution time : {predicted_execution_time}s')
        start_time = time.time()
        data_processor = DataProcessor(analyzer, clusterer)
        data_processor.setup_visualization_data(args.save)
        logger.debug(f'STEP 5/5 Executed in {time.time() - start_time}s\n')

    logger.info('Visualization web server running at localhost:8000')
    logger.info('Open localhost:8000 in your browser to view the visualization')
    run_webserver()
    

if __name__ == "__main__":

    main()
