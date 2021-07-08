import pydriller
import nx
import os
import tqdm
import atexit

class AnalysisManager:

    def __init__(self, args):
        """ Downloads the repo in a temp folder if it is not stored locally.
        Create a repository mining object to later analyze the commits.
        Registers a function to supress the temp folder at the end of the execution
        if the repo was stored remotely.

        Attributes :
            url : url of the repo (either remote or local)
            repo_folder : folder where repo is stored (same as url if local repo)
            repository_mining : Repository object to analyze the repo
            git_repo : Git object
            repo_files_path : list of paths to the files contained in the repo
            repo_files : list of files contained in the repo
            total_commits : total number of commits
            commit_graph : networkx graph object of files in the repo
            filename_to_path : dict to get path of file in repo given its name
            path_prefix : path prefix specific to the computer you are using
            _tmp_dir : location of temp directory
        """

        self.args = args

        self.url = args.url

        # Clone repo if necessary
        if self._is_remote_repository(url):
            self.repo_folder = self._clone_remote_repository(self._clone_folder(), url)
        else:
            self.repo_folder = url

        # Get a Repository object
        self.repository_mining = pydriller.Repository(self.repo_folder, num_workers=1)

        # Get a Git object
        self.git_repo = pydriller.Git(self.repo_folder)
        self.total_commits = self.git_repo.total_commits()
        

        # Create graph of all commits
        self.commit_graph = nx.Graph()

        # Commits
        self.commits = []

        # Get list of files
        self.forbidden_file_extensions = ['.zip', '.gif', '.png']
        repo_files_paths = self.git_repo.files()
        self.path_prefix = os.path.commonpath(repo_files_paths)
        self.repo_files_path = []
        for file_path in repo_files_paths:
            _, file_extension = os.path.splitext(file_path)
            if file_extension not in self.forbidden_file_extensions:
                file_path = file_path[len(self.path_prefix)+1:]
                self.repo_files_path.append(file_path)
        self.commit_graph.add_nodes_from([(file_path, {'number_modifications': 0, 'index': file_path}) for file_path in self.repo_files_path])
        
        # Find earlier names and paths of these files
        self.old_to_new_path = {}
        pbar = tqdm.tqdm(total=self.total_commits)
        for commit in self.repository_mining.traverse_commits():
            self.commits.append(commit)
            for modification in commit.modified_files:
                if modification.old_path != modification.new_path and modification.old_path is not None:
                    self.old_to_new_path[modification.old_path] = modification.new_path
            pbar.update(1)
        pbar.close()
        
        # Remove temp folder at end of execution
        atexit.register(self._cleanup)


    def retrieve_current_path(self, old_path):
        """ Recursively retrieves the current path, given a (potentially)
        old path.
        """

        path = old_path
        detect_endless_loop = 0

        while path is not None and path not in self.repo_files_path and detect_endless_loop < 50:
            if path in self.old_to_new_path:
                path = self.old_to_new_path[path]
            else:
                path = None
            detect_endless_loop += 1

        return path
    
    @staticmethod
    def _is_remote_repository(repo: str) -> bool:
        """ Checks wether or not repo is a local or remote path
        to a repo.
        """

        return repo.startswith("git@") or repo.startswith("https://")

    def _clone_remote_repository(self, path_to_folder: str, repo: str) -> str:
        """ Clones the remote repo to path_to_folder.
        """

        repo_folder = os.path.join(path_to_folder, self._get_repo_name_from_url(repo))
        git.Repo.clone_from(url=repo, to_path=repo_folder)

        return repo_folder

    def _clone_folder(self) -> str:
        """ Create and returns a temporary folder.
        """

        self._tmp_dir = tempfile.TemporaryDirectory()
        clone_folder = self._tmp_dir.name
        # print(clone_folder)

        return clone_folder

    @staticmethod
    def _get_repo_name_from_url(url: str) -> str:
        """ Parses repo url to get its name.
        """

        last_slash_index = url.rfind("/")
        last_suffix_index = url.rfind(".git")
        if last_suffix_index < 0:
            last_suffix_index = len(url)

        if last_slash_index < 0 or last_suffix_index <= last_slash_index:
            raise Exception("Badly formatted url {}".format(url))

        return url[last_slash_index + 1:last_suffix_index]

    def _cleanup(self):
        """ Cleanup temporary folder at the end of execution.
        """

        if self._is_remote_repository(self.url):
            assert self._tmp_dir is not None
            try:
                self._tmp_dir.cleanup()
            except PermissionError:
                # on Windows, Python 3.5, 3.6, 3.7 are not able to delete
                # git directories because of read-only files.
                # In this case, just ignore the errors.
                shutil.rmtree(self._tmp_dir.name, ignore_errors=True)

    def save_graph(self, G, path):
        """ Saves a graph in the pickle format.
        """

        nx.readwrite.gpickle.write_gpickle(G, path)

    def load_commit_graph(self, path):
        """ Loads a commit graph stored in the pickle format.
        """

        self.commit_graph = nx.readwrite.gpickle.read_gpickle(path)

        
    def find_lines_related_to_function(self, function_name, path):
        """ Find the lines related to a given function and print them.
        """

        modified_in_commits = self.get_commits_that_modified_function(function_name, path)
        self.find_related_lines(path, modified_in_commits)

    def find_lines_related_to_lines(self, start_line, end_line, path, concurrent=False):
        """ Find lines in other files that are related to line in a given file,
        based on commit history.
        """
        cwd = os.getcwd()
        os.chdir(self.repo_folder)

        modified_in_commits = self.get_commits_that_modified_line(start_line, end_line, path)
        modified_in_commits = [commit[1:-1] for commit in modified_in_commits]

        if concurrent:
            self.find_related_lines_concurrent(path, modified_in_commits)
        else:
            self.find_related_lines(path, modified_in_commits)

        os.chdir(cwd)
        
    def find_related_lines(self, path, modified_in_commits):
        

        related_lines = {}
        line_history = {}

        for commit in pydriller.Repository(self.repo_folder, only_commits=modified_in_commits).traverse_commits():

            for modification in tqdm.tqdm(commit.modified_files):

                path = path.replace("/", "\\")
                if modification.new_path in self.repo_files_path:
                    current_path = modification.new_path
                else:
                    current_path = self.retrieve_current_path(modification.new_path)
                if current_path is not None and modification.new_path[-4:] not in self.forbidden_file_extensions and current_path != path:

                    print(modification.new_path)
                    # Get path to file to count number of lines
                    filepath = self.repo_folder + '\\' + current_path
                    if os.path.getsize(filepath):
                        with open(filepath, 'rb') as f:
                            for i, _ in enumerate(f):
                                pass
                            linenumber = i + 1
                    else:
                        linenumber = 0
                    # Split file in group of 10 lines and check of they are linked to the modified line
                    if linenumber > 0:
                        self.get_related_lines_precise(related_lines, linenumber, current_path, commit.hash, line_history)

        print(related_lines)
        self.display_related_lines(related_lines, len(modified_in_commits))

    def find_related_lines_concurrent(self, path, modified_in_commits):

        related_lines = {}
        line_history = {}
        related_files = {}

        for commit in pydriller.Repository(self.repo_folder, only_commits=modified_in_commits).traverse_commits():

            for modification in commit.modified_files:

                path = path.replace("/", "\\")
                if modification.new_path in self.repo_files_path:
                    current_path = modification.new_path
                else:
                    current_path = self.retrieve_current_path(modification.new_path)
                if current_path not in related_files:
                    if current_path is not None and modification.new_path[-4:] not in self.forbidden_file_extensions and current_path != path:

                        # Get path to file to count number of lines
                        filepath = self.repo_folder + '\\' + current_path
                        if os.path.getsize(filepath):
                            with open(filepath, 'rb') as f:
                                for i, _ in enumerate(f):
                                    pass
                                linenumber = i + 1
                        else:
                            linenumber = 0
                        related_files[current_path] = linenumber

        file_lines = []
        for filepath, linenumber in related_files.items():
            for line in range(1, linenumber+1):
                file_lines.append((filepath, line))

        
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            future_to_line = {executor.submit(self.analyze_line, file_line): file_line for file_line in file_lines}

            pbar = tqdm.tqdm(total=len(file_lines))
            for future in concurrent.futures.as_completed(future_to_line):
                file_line = future_to_line[future]
                try:
                    modified_in_commits_2 = future.result()
                    modified_in_commits_2 = [commit[1:-1] for commit in modified_in_commits_2]
                    if file_line[0] not in related_lines:
                        related_lines[file_line[0]] = {file_line[1]:len(set(modified_in_commits_2).intersection(set(modified_in_commits)))}
                    else:
                        related_lines[file_line[0]][file_line[1]] = len(set(modified_in_commits_2).intersection(set(modified_in_commits)))
                except Exception as exc:
                    print(f'Error during execution : {exc}')
                pbar.update(1)
            pbar.close()


        print(related_lines)
        self.display_related_lines(related_lines, len(modified_in_commits))
      

    def get_related_lines_fast(self, related_lines, linenumber, file_path, commit_hash):

        for i in range(1, linenumber, 10):
            if i + 10 > linenumber:
                modified_in_commits2 = self.get_commits_that_modified_line(i, linenumber, file_path)
            else:
                modified_in_commits2 = self.get_commits_that_modified_line(i, i+9, file_path)
        
            if commit_hash in modified_in_commits2:
                if file_path in related_lines:
                    if i not in related_lines[file_path]:
                        for j in range(10):
                            related_lines[file_path][i+j] += 1
                    else:
                        for j in range(10):
                            related_lines[file_path][i+j] = 1
                    if not self.interval_contained_in_list(related_lines[file_path], (i, i+9)):
                        self.insert_interval_in_list(related_lines[file_path], (i, i+9))
                else:
                    related_lines[file_path] = {i:1}
                    for j in range(1, 10):
                            related_lines[file_path][i+j] = 1
                    


    def get_related_lines_precise(self, related_lines, linenumber, file_path, commit_hash, line_history):

        if file_path not in line_history:
            line_history[file_path] = {}
            for i in range(1, linenumber):
                modified_in_commits2 = self.get_commits_that_modified_line(i, i, file_path)
                line_history[file_path][i] = modified_in_commits2

        for i in range(1, linenumber):
            if commit_hash in line_history[file_path][i]:
                if file_path in related_lines:
                    if i in related_lines[file_path]:
                        related_lines[file_path][i] += 1
                    else:
                        related_lines[file_path][i] = 1
                    
                else:
                    related_lines[file_path] = {i:1}

    @staticmethod
    def display_related_lines(related_lines, num_modifications):

        most_correlated_lines = []

        for file_path in related_lines:

            file_correlation_string = ''
            file_correlation_string += f'File {file_path}'
            lines = []
            for key in related_lines[file_path]:
                lines.append(key)
                most_correlated_lines.append((key, file_path, related_lines[file_path][key], f'{100*related_lines[file_path][key]/num_modifications}%'))
            lines.sort()
            start, end = lines[0], lines[0]
            for i in range(1, len(lines)):
                if lines[i] == end + 1:
                    end += 1
                else:
                    file_correlation_string += f' {start}-{end}'
                    start, end = lines[i], lines[i]
            file_correlation_string += f' {start}-{end}'
            print(file_correlation_string)

        most_correlated_lines.sort(key=lambda x: (-x[2], x[1], x[0]), reverse=False)
        for (line, file_path, num_modifications_line, correlation) in most_correlated_lines:
            print(f'Line {line} of {file_path} is {correlation} correlated ({num_modifications_line} modifs)')
                    


    def get_commits_that_modified_line(self, start_line, end_line, path):
        """ Get a list of commits in which the given lines of a given file were modified.
        """
        history = subprocess.run(['git', 'log', '-L', f'{start_line},{end_line}:{path}', '--format=\"%H\"', '-s'], capture_output=True, encoding='utf_8').stdout.split('\n')
        modified_in_commits = [line for line in history if len(line) > 0]
    
        '''
        for line in history:
            if line[0:6] == 'commit':
                modified_in_commits.append(line[7:])
        '''
        
        return modified_in_commits

    def get_commits_that_modified_function(self, function_name, path):
        """ Get a list of commits in which a function was modified.
        """


        history = subprocess.run(['git', 'log', '-L', f':{function_name}:{path}', '--format=\"%H\"', '-s'], capture_output=True, encoding='utf_8').stdout.split('\n')
        modified_in_commits = [line for line in history if len(line) > 0]
        
        return modified_in_commits
                    
    @staticmethod
    def interval_contained_in_list(list_intervals, interval):
        """ Checks if an interval is contained in a list of intervals.
        """

        for (a, b) in list_intervals:

            if a <= interval[0] and interval[1] <= b:
                return True
        
        return False

    @staticmethod
    def insert_interval_in_list(list_intervals, interval):
        """ Inserts an interval in a list of intervals.
        """

        merge_left, merge_right = False, False
        for (a, b) in list_intervals:
            if b == interval[0] - 1:
                merge_left = True
                merge_left_pair = (a, b)
            if a == interval[1] + 1:
                merge_right = True
                merge_right_pair = (a, b)
        if merge_left and merge_right:
            list_intervals.remove(merge_left_pair)
            list_intervals.remove(merge_right_pair)
            list_intervals.append((merge_left_pair[0], merge_right_pair[1]))
        elif merge_left:
            list_intervals.remove(merge_left_pair)
            list_intervals.append((merge_left_pair[0], interval[1]))
        elif merge_right:
            list_intervals.remove(merge_right_pair)
            list_intervals.append((interval[0], merge_right_pair[1]))
        else:
            list_intervals.append(interval)


    def analyze_correlation(self, 
                        treecommit_analysis=False, 
                        commit_analysis=False, 
                        commit_lines_analysis=False, 
                        concurrent=False,
                        single_line=None,
                        get_dataframe=False,
                        get_commit_to_files_dict=False,
                        get_dates=False):
        """ Find files/folders that are modified together (ie. in same commit).
        Update commit and TreeCommit graphs accordingly.
        """


        if treecommit_analysis or commit_analysis:

            # Initialize variables to create a dataframe containing the commits
            files_commits = {}
            current_length = 0
            columns = []

            files_modifications_date = {}

            commit_to_files = {}

            pbar = tqdm.tqdm(total=self.total_commits)
            for commit in self.commits:

                commit_date = commit.committer_date

                current_length += 1
                columns.append(commit.hash)

                modified_files = []
                for modification in commit.modified_files:

                    if modification.new_path in self.repo_files_path:
                        current_path = modification.new_path
                    else:
                        current_path = self.retrieve_current_path(modification.new_path)

                    if current_path is not None:

                        modified_files.append(current_path)

                        # Saving dates
                        if get_dates:
                            if current_path not in files_modifications_date:
                                files_modifications_date[current_path] = {'creation_date': commit_date, 'last_modification': commit_date}
                            else:
                                files_modifications_date[current_path]['last_modification'] = commit_date

                        # Updating dataframe data
                        if get_dataframe:
                            if current_path in files_commits:

                                while len(files_commits[current_path]) < current_length - 1:
                                    files_commits[current_path].append(0)
                                files_commits[current_path].append(1)
                            
                            else:
                                files_commits[current_path] = [0 for _ in range(current_length-1)]
                                files_commits[current_path].append(1)

                if get_commit_to_files_dict:
                    commit_to_files[commit.hash] = modified_files

                pairs_of_modified_files = []
                for i in range(len(modified_files)):
                    for j in range(i+1, len(modified_files)):
                        pairs_of_modified_files.append((modified_files[i], modified_files[j]))

                # TreeCommit Graph
                if treecommit_analysis:
                    self.analyze_correlation_treecommit_graph(pairs_of_modified_files)

                # Commit Graph
                if commit_analysis:
                    self.analyze_correlation_commit_graph(modified_files, pairs_of_modified_files)

                pbar.update(1)
            pbar.close()

            outputs = []

            # Create dataframe
            if get_dataframe:
                dataframe_list = []
                index = []
                for key, value in files_commits.items():

                    if len(value) < current_length:

                        while len(files_commits[key]) < current_length:
                                files_commits[key].append(0)

                    index.append(key)
                    dataframe_list.append(value)
                
                df = pd.DataFrame(dataframe_list, index=index, columns=columns)
                outputs.append(df)

            if get_commit_to_files_dict:
                outputs.append(commit_to_files)

            if get_dates:
                outputs.append(files_modifications_date)

            return outputs

        # Commit Graph lines
        if commit_lines_analysis:
            if concurrent:
                self.analyze_correlation_commit_lines_graph_concurent(single_line=single_line)
            else:
                self.analyze_correlation_commit_lines_graph()

    def analyze_correlation_commit_graph(self, modified_files, pairs_of_modified_files):
        """ Find files that are modified together (ie. in same commit).
        Create an edge between them, and update its value.
        """

        for modified_file in modified_files:

            if modified_file in self.commit_graph.nodes:
                self.commit_graph.nodes[modified_file]['number_modifications'] += 1

        for edge in pairs_of_modified_files:

            if edge[0] in self.commit_graph.nodes and edge[1] in self.commit_graph.nodes:
                if self.commit_graph.has_edge(edge[0], edge[1]):
                    self.commit_graph.edges[edge[0], edge[1]]['number_modifications_same_commit'] += 1
                else:
                    self.commit_graph.add_edge(edge[0], edge[1], number_modifications_same_commit=1)




    @staticmethod
    def get_file_number_of_lines(file_path):
        """ Count the number of lines in a file.
        """
        
        if os.path.getsize(file_path):
            with open(file_path, 'rb') as f:
                for i, _ in enumerate(f):
                    pass
                linenumber = i + 1
        else:
            linenumber = 0

        return linenumber



    def analyze_line(self, file_line):
        """ Returns the commits in which a line was modified.
        """

        file_path, line = file_line

        return self.get_commits_that_modified_line(line, line, file_path)

    def analyze_method(self, file_method):
        """ Returns the commits in which a function was modified.
        """

        file_path, method = file_method

        return self.get_commits_that_modified_function(method, file_path)



    def compute_correlation(self, node_name, commit_graph, method='basic', alpha=0.5):
        """ Compute correlation between a file and another one in commit graph based on value of edge.
        Correlation = Value of edge / max value of edge for this node
        """

        number_modifications = commit_graph.nodes[node_name]["number_modifications"]
        neighbors_correlation = []

        for neighbor in commit_graph.neighbors(node_name):

            number_modifications_same_commit = commit_graph.edges[node_name, neighbor]["number_modifications_same_commit"]
            number_modifications_neighbor = commit_graph.nodes[neighbor]["number_modifications"]

            if method == 'basic':
                correlation = Correlation.Correlation.basic_correlation(number_modifications_same_commit, number_modifications)

            elif method == 'addition':

                correlation = Correlation.Correlation.addition_correlation(number_modifications_same_commit, number_modifications, number_modifications_neighbor, alpha)
            
            elif method == 'multiplication':

                correlation = Correlation.Correlation.multiplication_correlation(number_modifications_same_commit, number_modifications, number_modifications_neighbor, alpha)

            neighbors_correlation.append((neighbor, correlation, number_modifications_same_commit))
        

        neighbors_correlation = self.parse_neighbors_correlation(neighbors_correlation)

        print(f'Correlation of {node_name} (modified in {number_modifications} commits) with :')
        for i, neighbor in enumerate(neighbors_correlation):
            if i < 200:
                print(f'{neighbor[0]}:{neighbor[1]} : {neighbor[2]}% (modified {neighbor[3]} times)')
            else:
                break


    def parse_neighbors_correlation(self, neighbors_correlation):
        """ Parses the neighbor_correlation object created in compute_correlation() to merge
        and remove useless intervals.
        """

        correlation_intervals = {}

        for neighbor, correlation, num_mod in neighbors_correlation:

            filepath, line = neighbor.split(':')
            line = int(line)

            if filepath not in correlation_intervals:
                correlation_intervals[filepath] = {(line, line):(correlation, num_mod)}
            else:
                merge_left, merge_right = False, False
                for (a, b) in correlation_intervals[filepath].keys():
                    if b == line - 1 and correlation_intervals[filepath][(a,b)][0] == correlation:
                        merge_left = True
                        merge_left_pair = (a, b)
                    if a == line + 1 and correlation_intervals[filepath][(a,b)][0] == correlation:
                        merge_right = True
                        merge_right_pair = (a, b)
                if merge_left and merge_right:
                    correlation_intervals[filepath].pop(merge_left_pair)
                    correlation_intervals[filepath].pop(merge_right_pair)
                    correlation_intervals[filepath][(merge_left_pair[0], merge_right_pair[1])] = (correlation, num_mod)
                elif merge_left:
                    correlation_intervals[filepath].pop(merge_left_pair)
                    correlation_intervals[filepath][(merge_left_pair[0], line)] = (correlation, num_mod)
                elif merge_right:
                    correlation_intervals[filepath].pop(merge_right_pair)
                    correlation_intervals[filepath][(line, merge_right_pair[1])] = (correlation, num_mod)
                else:
                    correlation_intervals[filepath][(line, line)] = (correlation, num_mod)


        neighbors_correlation_packed = []
        for filepath, linedict in correlation_intervals.items():
            for line_interval, data in linedict.items():
                neighbors_correlation_packed.append((filepath, line_interval, data[0], data[1]))
        
        neighbors_correlation_packed.sort(key=lambda x: (-x[2], x[0], x[1][0]), reverse=False)

        return neighbors_correlation_packed



    def compute_same_level_correlation(self, node_path):
        """ Compute correlation between a file/folder and another one in commit TreeGraph based on value of edge.
        Correlation = Value of edge / max value of edge for this node
        """

        def compute_same_level_correlation_iteration(tree_graph, splitted_path):

            if len(splitted_path) == 1 and splitted_path[0] in tree_graph.kids:
                self.compute_correlation(splitted_path[0], tree_graph.graph)
            elif len(splitted_path) > 1 and splitted_path[0] in tree_graph.kids:
                compute_same_level_correlation_iteration(tree_graph.kids[splitted_path[0]], splitted_path[1:])


        tree_graph = self.commit_tree_graph

        splitted_path = node_path.split('\\')
        print(splitted_path)

        compute_same_level_correlation_iteration(tree_graph, splitted_path)

    def compute_files_that_should_be_in_commit(self, commit_hash):
        """ Returns a dictionnary containing for each file a score saying if it should be included
        in a given commit.
        """

        similar_commits = {}
        potential_nodes = set()

        # Get list of files modified in commit
        modified_files = []
        modified_files_dict = {}
        for commit in pydriller.Repository(self.repo_folder, single=commit_hash).traverse_commits():
            for modification in commit.modified_files:
                modified_files.append(modification.new_path)
                modified_files_dict[modification.new_path] = 1

        # Compute each commit similarity score
        print('Computing similarity score')
        for commit in tqdm.tqdm(pydriller.Repository(self.repo_folder).traverse_commits()):
            if commit.hash != commit_hash:
                modified_files_other_commit = []
                new_nodes = []
                similar_nodes = 0
                for modification in commit.modified_files:

                    if modification.new_path in self.repo_files_path:
                        current_path = modification.new_path
                    else:
                        current_path = self.retrieve_current_path(modification.new_path)

                    if current_path is not None and current_path in modified_files_dict:
                        similar_nodes += 1
                    else:
                        new_nodes.append(current_path)
                    modified_files_other_commit.append(current_path)
                similarity = similar_nodes / max(len(modified_files), len(modified_files_other_commit))
                if similarity > 0.3:
                    similar_commits[commit.hash] = (similarity, new_nodes)
                    for node in new_nodes:
                        if node not in potential_nodes:
                            potential_nodes.add(node)

        # Compute score of new potential nodes
        print('Compute node scores')
        for node in tqdm.tqdm(potential_nodes):
            node_score = 0
            for _, (similarity, nodes) in similar_commits.items():
                if node in nodes:
                    node_score += similarity
            node_score /= len(similar_commits)
            modified_files_dict[node] = node_score

        for node in self.repo_files_path:
            if node not in modified_files_dict:
                modified_files_dict[node] = 0

        return modified_files_dict

    def create_commits_dataframe(self):
        """ Create a dataframe, with files as rows, commits as columns. The value
        in a cell is 0 if a file was not in a commit, 1 otherwise.
        """

        files_commits = {}
        current_length = 0
        columns = []

        pbar = tqdm.tqdm(total=self.total_commits)
        for commit in self.repository_mining.traverse_commits():

            current_length += 1
            columns.append(commit.hash)

            for modification in commit.modified_files:

                if modification.new_path in self.repo_files_path:
                    current_path = modification.new_path
                else:
                    current_path = self.retrieve_current_path(modification.new_path)
                
                if current_path is not None:

                    if current_path in files_commits:

                        while len(files_commits[current_path]) < current_length - 1:
                            files_commits[current_path].append(0)
                        files_commits[current_path].append(1)
                    
                    else:
                        files_commits[current_path] = [0 for _ in range(current_length-1)]
                        files_commits[current_path].append(1)

            pbar.update(1)
        pbar.close()

        dataframe_list = []
        index = []
        for key, value in files_commits.items():

            if len(value) < current_length:

                while len(files_commits[key]) < current_length:
                        files_commits[key].append(0)

            index.append(key)
            dataframe_list.append(value)

        return pd.DataFrame(dataframe_list, index=index, columns=columns)


    def create_commits_dataframe_lines(self):
        """ Same as create_commits_dataframe() but with lines as rows instead of files.
        """

        columns = []

        pbar = tqdm.tqdm(total=self.total_commits)
        for commit in self.repository_mining.traverse_commits():

            columns.append(commit.hash)

            pbar.update(1)
        pbar.close()


        dataframe_list = []
        index = []


        cwd = os.getcwd()
        os.chdir(self.repo_folder)


        # Print analyzing all the lines of the repo
        print('Print analyzing all the lines of the repo')
        file_lines = []
        

        for file_path in tqdm.tqdm(self.repo_files_path):

            # Get path to file and count number of lines
            complete_file_path = self.repo_folder + '\\' + file_path
            linenumber = self.get_file_number_of_lines(complete_file_path)

            for i in range(1, linenumber):
                file_lines.append((file_path, i))

        line_to_commits = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            future_to_line = {executor.submit(self.analyze_line, file_line): file_line for file_line in file_lines}

            pbar = tqdm.tqdm(total=len(file_lines))
            for future in concurrent.futures.as_completed(future_to_line):
                file_line = future_to_line[future]
                try:
                    
                    modified_in_commits = future.result()
                    modified_in_commits = [commit[1:-1] for commit in modified_in_commits]
                    index.append(f'{file_line[0]}:{file_line[1]}')
                    file_line_commits = []
                    for commit in columns:
                        if commit in modified_in_commits:
                            file_line_commits.append(1)
                        else:
                            file_line_commits.append(0)
                    dataframe_list.append(file_line_commits)
                except Exception as exc:
                    print(f'Error during execution : {exc}')
                pbar.update(1)
            pbar.close()


        os.chdir(cwd)

        return pd.DataFrame(dataframe_list, index=index, columns=columns)

    def find_methods_in_python_file(self, file_path):
        """ Returns a list of the names of all the methods included in 
        a python file.
        """

        methods = []
        o = open(file_path, "r", encoding='utf-8')
        text = o.read()
        p = ast.parse(text)
        for node in ast.walk(p):
            if isinstance(node, ast.FunctionDef):
                methods.append(node.name)

        print(methods)
        return methods


    def create_commits_dataframe_functions(self):
        """ Same as create_commits_dataframe() but with functions instead of files as rows.
        """

        columns = []

        pbar = tqdm.tqdm(total=self.total_commits)
        for commit in self.repository_mining.traverse_commits():

            columns.append(commit.hash)

            pbar.update(1)
        pbar.close()


        dataframe_list = []
        index = []


        cwd = os.getcwd()
        os.chdir(self.repo_folder)

        with open('./gitattributes', 'a') as f:
            f.write('*.py   diff=python\n')

        print(os.listdir('./'))
        

        # Print analyzing all the lines of the repo
        print('Print analyzing all the lines of the repo')
        file_methods = []
        

        for file_path in tqdm.tqdm(self.repo_files_path):

            if file_path[-3:] == '.py':

                print(file_path)
                # Get path to file and count number of lines
                complete_file_path = self.repo_folder + '\\' + file_path
                methods = self.find_methods_in_python_file(complete_file_path)

                for method in methods:
                    file_methods.append((file_path, method))

        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            future_to_method = {executor.submit(self.analyze_method, file_method): file_method for file_method in file_methods}

            pbar = tqdm.tqdm(total=len(file_methods))
            for future in concurrent.futures.as_completed(future_to_method):
                file_method = future_to_method[future]
                try:
                    
                    modified_in_commits = future.result()
                    modified_in_commits = [commit[1:-1] for commit in modified_in_commits]
                    row_name = f'{file_method[0]}:{file_method[1]}'
                    if row_name not in index:
                        index.append(f'{file_method[0]}:{file_method[1]}')
                        file_method_commits = []
                        for commit in columns:
                            if commit in modified_in_commits:
                                file_method_commits.append(1)
                            else:
                                file_method_commits.append(0)
                        dataframe_list.append(file_method_commits)
                except Exception as exc:
                    print(f'Error during execution : {exc}')
                pbar.update(1)
            pbar.close()


        os.chdir(cwd)

        return pd.DataFrame(dataframe_list, index=index, columns=columns)

    def create_commits_dataframe2(self):
        """ DEPRECATED.
        Creates a dataframe with files as rows, and engineered features as columns.
        """

        columns = ['num_commits', 
                    #'average_num_files_in_commits',
                    'number_of_neighbors',
                    'average_num_modif_with_neighbors']
        df = pd.DataFrame(columns=columns)

        for filename in self.repo_files_path:

            num_commits = self.commit_graph.nodes[filename]['number_modifications']
            total_connections = 0
            num_neighbors = 0
            for neighbor in self.commit_graph[filename]:
                num_neighbors += 1
                total_connections += self.commit_graph.edges[filename, neighbor]['number_modifications_same_commit']
            average_num_modif_with_neighbor = total_connections/num_neighbors if num_neighbors > 0 else 0
            data = [num_commits, num_neighbors, average_num_modif_with_neighbor]

            df.loc[filename] = data

        return df

    def dimensionality_reduction(self, df, method='tSNE'):
        """ Performs a dimensionality reduction on a given dataframe, using the given method.
        """

        if method == 'tSNE':
            tsne = sklearn.manifold.TSNE(n_components=2, perplexity=5, metric='precomputed')
            embedded_data = tsne.fit_transform(df)

        elif method == 'MCA':
        
            df.replace({0: "False", 1: "True"}, inplace = True)
            mca = prince.MCA(n_components=2)
            embedded_data = mca.fit_transform(df)

        elif method == 'NMDS':

            nmds = sklearn.manifold.MDS(n_components=2, metric=False, max_iter=3000, eps=1e-12,
                    dissimilarity="precomputed",
                    n_init=1)
            embedded_data = nmds.fit_transform(df)

        df_embedded = pd.DataFrame(embedded_data, index=df.index)
        return df_embedded

    def get_distance_matrix(self, df):
        """ Computes a distance matrix using the jaccard distance on the inputed dataframe.
        """

        dist = sklearn.neighbors.DistanceMetric.get_metric('jaccard')
        distance_matrix = dist.pairwise(df.iloc[:,:].to_numpy())
        print(f'Distance matrix : {distance_matrix}')
        print(f'{len(distance_matrix)}, {len(distance_matrix[0])}')

        distance_df = pd.DataFrame(distance_matrix, index=df.index, columns=df.index)

        return distance_df

    def cluster_dataframe(self, df, method='HDBSCAN', distance_matrix=True, min_size=2, max_eps=None, join_clusterless_samples=True):
        """ Clusters a dataframe using a given method.
        """

        if method == 'HDBSCAN':

            clusterer = hdbscan.HDBSCAN(min_cluster_size=2, cluster_selection_epsilon=0.5)
            clusterer.fit(df)
        
        elif method == 'OPTICS':

            if distance_matrix:
                if max_eps is not None:
                    clusterer = sklearn.cluster.OPTICS(min_samples=min_size, metric='precomputed', n_jobs=4, max_eps=max_eps)
                else:
                    clusterer = sklearn.cluster.OPTICS(min_samples=min_size, metric='precomputed', n_jobs=4)
            else:
                clusterer = sklearn.cluster.OPTICS(min_samples=min_size, n_jobs=4)
            clusterer.fit(df)

        elif method == 'AggClustering':

            if distance_matrix:
                clusterer = sklearn.cluster.AgglomerativeClustering(
                        n_clusters=None,
                        affinity='precomputed',
                        linkage='average',
                        distance_threshold=0.95)
            else:
                clusterer = clusterer = sklearn.cluster.AgglomerativeClustering(
                        n_clusters=None,
                        distance_threshold=1)
            clusterer.fit(df)

        elif method == 'BIRCH':

            if distance_matrix:
                clusterer = sklearn.cluster.Birch(
                        n_clusters=None)
            else:
                clusterer = sklearn.cluster.Birch(
                        n_clusters=None,
                        affinity='precomputed',
                        distance_threshold=1)
            clusterer.fit(df)

        

        filenames = df.index.tolist()
        clusters = {}

        cluster_labels = []

        if not join_clusterless_samples:
            backwards_index = -1

        for (filename, cluster) in zip(filenames, clusterer.labels_):

            filename = filename.replace("/", "\\")

            if not join_clusterless_samples and cluster == -1:
                cluster = backwards_index
                backwards_index -= 1
            
            cluster_labels.append(cluster)
            
            if cluster in clusters:
                clusters[cluster].append(filename)
            else:
                clusters[cluster] = [filename]

        return clusters, cluster_labels

    def count_clusters_common_commits(self, df, clusters, lines=False):
        """ Counts the number of common commits between two clusters.
        Takes a dataframe containing the commits as columns and the files/lines/... as rows.
        Takes a dict containing the clusters.
        """

        clusters_extended = {}

        for key, value in clusters.items():

            number_common_commits = 0

            for column in df:

                number_common_files_commit = 0
                for filename in value:

                    if df.loc[filename, column] == 1:

                        number_common_files_commit += 1

                if number_common_files_commit == len(value):
                    number_common_commits += 1

            if lines:
                value = self.parse_fileline(value)
            
            clusters_extended[key] = (number_common_commits, value)
            # print(f'Cluster {key}, {number_common_commits} common commits : {value}\n')

        return clusters_extended

    def display_df(self, df, clusters_labels):
        """ Displays a 2D dataframe as a scatter plot using matplotlib.
        """

        X = df.iloc[:, 0]
        Y = df.iloc[:, 1]

        _, ax = plt.subplots()
        ax.scatter(X, Y, c=clusters_labels)

        for i, txt in enumerate(clusters_labels):
            ax.annotate(txt, (X[i], Y[i]))

        # plt.scatter(X, Y, c=clusters_labels)
        plt.show()
                    
    def print_commits(self):
        """ Print all the commits of a repo.
        """

        for commit in self.repository_mining.traverse_commits():
            print(f'Commit : {commit.hash}')
            print(f'Parents : {commit.parents}')

    def analyze_clusters(self, clusters):


        print('Starting cluster analysis')
        cluster_to_files = {}
        file_to_cluster = {}

        for cluster_number, values in clusters.items():

            parsed_values = self.parse_fileline(values)
            cluster_to_files[cluster_number] = parsed_values

            for file_line in values:

                file_path, _ = file_line.split(":")
                
                if file_path not in file_to_cluster:
                    file_to_cluster[file_path] = [cluster_number]
                elif cluster_number not in file_to_cluster[file_path]:
                    file_to_cluster[file_path].append(cluster_number)

        '''
        # print(f'Cluster to files : {cluster_to_files}\n\n')
        print(f'File to clusters : {file_to_cluster}')

        for key, value in cluster_to_files.items():
            print(f'Cluster number {key} : {value}')
        '''

    def parse_fileline(self, files_lines):

        beautiful_files_lines = {}

        for file_line in files_lines:

            file_path, line = file_line.split(":")

            if file_path not in beautiful_files_lines:
                beautiful_files_lines[file_path] = [int(line)]
            else:
                beautiful_files_lines[file_path].append(int(line))

        for file_path, lines in beautiful_files_lines.items():

            lines.sort()
            joined_lines = []

            start = lines[0]
            end = lines[0]
            for i in range(1, len(lines)):
                if lines[i] == end + 1:
                    end += 1
                else:
                    joined_lines.append((start, end))
                    start = lines[i]
                    end = lines[i]
            joined_lines.append((start,end))
            beautiful_files_lines[file_path] = joined_lines

        return beautiful_files_lines


    def rearchitecture_clusters(self, clusters_extended, df):
        """ Prints refactoring proposition given clusters and a dataframe containing
        files/lines/... as rows and commits as columns."""

        interesting_clusters = {}
        pool_of_lines = {}

        print('\n\nInteresting clusters')
        for cluster, value in clusters_extended.items():
            if value[0] >= 2 and len(value[1]) >= 2:
                print(f'Cluster {cluster}, num common mod {value[0]} : {value[1]}')
                interesting_clusters[cluster] = value
            else:
                for file_path in value[1].keys():
                    if file_path not in pool_of_lines:
                        pool_of_lines[file_path] = []

                    for line in value[1][file_path]:
                        pool_of_lines[file_path].append(line)



        print('\n\n')
        print(clusters_extended[0][1])
        
        for cluster_number, (num_mod, files_lines) in interesting_clusters.items():

            for file_path in files_lines.keys():
                if file_path in pool_of_lines:
                    for line in pool_of_lines[file_path]:
                        interesting_clusters[cluster_number][1][file_path].append(line)
                    
                    lines_to_be_sorted = interesting_clusters[cluster_number][1][file_path]
                    lines_to_be_sorted.sort(key=lambda x: x[0])

                    joined_lines = []

                    start = lines_to_be_sorted[0][0]
                    end = lines_to_be_sorted[0][1]
                    for i in range(1, len(lines_to_be_sorted)):
                        if lines_to_be_sorted[i][0] == end + 1:
                            end = lines_to_be_sorted[i][1]
                        else:
                            joined_lines.append((start, end))
                            start = lines_to_be_sorted[i][0]
                            end = lines_to_be_sorted[i][1]
                    joined_lines.append((start,end))
                    interesting_clusters[cluster_number][1][file_path] = joined_lines
        
        print('\n\nExtended clusters')
        for cluster, value in interesting_clusters.items():
            print(f'Cluster {cluster}, num common mod {value[0]} : {value[1]}')


        print('\n\nMerging clusters\n\n')

        initial_entropy = self.compute_entropy(self.commit_graph)
        print(f'Initial entropy : {initial_entropy}\n\n')

        for cluster, value in interesting_clusters.items():
            print(f'Entropy gain of cluster {cluster} merge')
            
            nodes = list(value[1].keys())

            new_node_name = nodes[0]
            new_commit_graph = copy.deepcopy(self.commit_graph)
            new_df = copy.deepcopy(df)

            for i in range(1, len(nodes)):
                new_commit_graph, new_df = self.merge_nodes(new_node_name, nodes[i], new_commit_graph, new_df)
                new_node_name += f':{nodes[i]}'
                
            new_entropy = self.compute_entropy(new_commit_graph)
            print(f'New entropy : {new_entropy}, gain : {new_entropy - initial_entropy}\n\n')


    def compute_file_lines(self, filename):
        """ Couts the number of lines in a file.
        """

        filepath = self.repo_folder + '\\' + filename
        if os.path.getsize(filepath):
            with open(filepath, 'rb') as f:
                for i, _ in enumerate(f):
                    pass
                lines = i + 1
        else:
            lines = 0

        return lines

    def compute_entropy(self, commit_graph):
        """ Compute the entropy of a commit graph.
        """

        # Entropy computation is not perfect
        # * New size won't be the sum of old sizes exactly
        # * We have to take into account the times when node1 and node2 were modified
        # together with one of their neighbor

        entropy = 0

        for node in commit_graph.nodes:


            # Compute number of lines
            if node in self.repo_files_path:
                lines = self.compute_file_lines(node)
            else:
                files = node.split(':')
                lines = 0
                for file in files:
                    lines += self.compute_file_lines(file)

            # Compute coupling with other nodes
            coupling = 0
            for neighbor in commit_graph.neighbors(node):
                coupling += commit_graph.edges[node, neighbor]['number_modifications_same_commit']


            entropy += lines * coupling

        return entropy

    
    def merge_nodes(self, node1, node2, initial_commit_graph, df):
        """ Merge nodes of commit graph.
        """

        new_commit_graph = copy.deepcopy(initial_commit_graph)

        # Etapes pour merger les nodes
        # 1. Get list of out connections with a dict
        # eg. {node3 : 5, node4 : 6}
        # 2. Get list of in connections with a dict
        # 3. Merge nodes

        # 1 and 2

        connections = {}

        index = list(df.index)
        new_node_row = []

        for column in df.columns:
            if df.at[node1, column] == 1 or df.at[node2, column] == 1:
                new_node_row.append(1)
                for neighbor in index:
                    if df.at[neighbor, column] == 1 and neighbor not in [node1, node2]:
                        if neighbor not in connections:
                            connections[neighbor] = 1
                        else:
                            connections[neighbor] += 1
            else:
                new_node_row.append(0)

        new_node_row = [new_node_row]


        '''
        for neighbor in initial_commit_graph.adj[node1]:
            if neighbor != node2:
                if neighbor not in connections:
                    connections[neighbor] = initial_commit_graph.edges[node1, neighbor]['number_modifications_same_commit']
                else:
                    connections[neighbor] += initial_commit_graph.edges[node1, neighbor]['number_modifications_same_commit']
        
        for neighbor in initial_commit_graph.adj[node2]:
            if neighbor != node1:
                if neighbor not in connections:
                    connections[neighbor] = initial_commit_graph.edges[node2, neighbor]['number_modifications_same_commit']
                else:
                    connections[neighbor] += initial_commit_graph.edges[node2, neighbor]['number_modifications_same_commit']
        '''


        new_commit_graph.remove_node(node1)
        new_commit_graph.remove_node(node2)

        new_node = f'{node1}:{node2}'
        new_commit_graph.add_node(new_node)

        new_row = pd.DataFrame(new_node_row, columns=list(df.columns), index=[new_node])
        new_df = df.drop(labels=[node1, node2])
        new_df = new_df.append(new_row)

        for neighbor, num_mod in connections.items():
            new_commit_graph.add_edge(new_node, neighbor)
            new_commit_graph.edges[new_node, neighbor]['number_modifications_same_commit'] = num_mod

        
        return new_commit_graph, new_df


    def display_interesting_clusters_extended(self, name):
        """ Prints the clusters contained in the file 'name'.
        """

                
        with open(name, "rb") as fp:
            clusters_extended = pickle.load(fp)

        interesting_clusters = 0
        for cluster, value in clusters_extended.items():
            modified_files = []
            for function in value[1]:
                file_name, _ = function.split(':')
                if file_name not in modified_files:
                    modified_files.append(file_name)
            
            if len(modified_files) > 1 and value[0] > 2:
                interesting_clusters += 1
                print(f'Cluster {cluster} ({value[0]} common commits) : {value[1]}')

        print(f'{interesting_clusters} interesting clusteres out of {len(clusters_extended)}')
        # print(clusters_extended)

    def draw_map(self, name, load_existing=False, join_clusterless_samples=True):
        """ Creates a .js file that can be visualized in Software as cities fashion.
        The visualization displays the logical couplings between files of a repo.
        """

        if not load_existing:
            df, commit_to_files, files_mod_dates = self.analyze_correlation(
                treecommit_analysis=False,
                commit_analysis=True,
                commit_lines_analysis=False,
                get_dataframe=True,
                get_commit_to_files_dict=True,
                get_dates=True)
            # df = self.create_commits_dataframe()
            df.to_csv(f'./df_{name}.csv')
        else:
            df = pd.read_csv(f'./df_{name}', index_col=0)

        if not load_existing:
            distance = self.get_distance_matrix(df)
            distance.to_csv(f'./df_distance_{name}.csv')
        else:
            distance = pd.read_csv(f'./df_distance_{name}.csv', index_col=0)
        
        clusters, clusters_labels = self.cluster_dataframe(
                    distance,
                    method='AggClustering',
                    distance_matrix=True,
                    min_size=3,
                    max_eps=1,
                    join_clusterless_samples=join_clusterless_samples)


        with open("./clusters_{name}.txt", "wb") as fp:
            pickle.dump(clusters, fp)        

        clusters_extended = self.count_clusters_common_commits(df, clusters, lines=False)
        print(clusters_extended)
        
        df_reduced = self.dimensionality_reduction(distance, method='tSNE')

        cluster_to_route = self.find_routes(clusters, df)
        cluster_centroid = self.find_centroids(df_reduced, clusters_labels)

        print(f'C to route : {cluster_to_route}')
        print(f'C c : {cluster_centroid}')

        sac_graph = self.create_software_as_cities_graph(cluster_to_route, cluster_centroid)

        print(f'Drawing')

        
        df["sum"] = df.sum(axis=1)

        citiesData = []
        for key in clusters_extended.keys():


            cityData = {}
            cityData['label'] = key
            cityData['centroid'] = {'x':cluster_centroid[key][0], 'y':cluster_centroid[key][1]}
            cityData['buildings'] = [{'height':df.loc[name, "sum"], 'fileName':name} for name in clusters_extended[key][1]]


            citiesData.append(cityData)

        CommitGraphDrawer.CommitGraphDrawer.draw_threejs(citiesData, cluster_to_route, commit_to_files, files_mod_dates)

        """
        drawer = CommitGraphDrawer.CommitGraphDrawer(sac_graph)
        # drawer.draw_commit_missing_files_bokeh(modified_files)
        drawer.draw_bokeh_software_as_cities(layout=cluster_centroid, routes=cluster_to_route)
        """

        # self.display_df(df_reduced, clusters_labels)

    def find_routes(self, clusters, df):
        """ Find the routes between clusters for a Software as Cities visualization.
        """

        cluster_to_commits = {}
        for cluster_number, cluster_files in clusters.items():
            cluster_to_commits[cluster_number] = []
            for cluster_file in cluster_files:
                for column in df.columns:
                    if df.loc[cluster_file, column] == 1:
                        cluster_to_commits[cluster_number].append(column)

        cluster_to_route = {}
        for cluster_a_number, cluster_a_commits in cluster_to_commits.items():
            for cluster_b_number, cluster_b_commits in cluster_to_commits.items():

                if cluster_a_number != cluster_b_number:
                    number_common_commits = len(set(cluster_a_commits).intersection(set(cluster_b_commits)))
                
                    if (cluster_a_number, cluster_b_number) not in cluster_to_route and number_common_commits > 0:
                        cluster_to_route[(cluster_a_number, cluster_b_number)] = number_common_commits

        return cluster_to_route

    def run_analysis():

        self.analysis.compute_couplings()
        self.analysis.get_distance_matrix()

    def find_centroids(self, df, clusters_labels):
        """ Find the centroids of the clusters in a Software as Cities visualization.
        """
        
        X = df.iloc[:, 0]
        Y = df.iloc[:, 1]

        cluster_points = {}
        for (x, y, label) in zip(X, Y, clusters_labels):

            if label not in cluster_points:
                cluster_points[label] = []
            cluster_points[label].append((x, y))

        cluster_centroid = {}
        for cluster_label, points in cluster_points.items():
            mean = [sum(ele) / len(points) for ele in zip(*points)]
            cluster_centroid[int(cluster_label)] = mean

        max_x = max([mean[0] for mean in cluster_centroid.values()])
        max_y = max([mean[1] for mean in cluster_centroid.values()])

        cluster_centroid = {cluster_label:(x/max_x, y/max_y) for cluster_label, (x,y) in cluster_centroid.items()}

        return cluster_centroid

    def create_software_as_cities_graph(self, cluster_to_route, cluster_centroid):
        """ Creates a 2D simplified Software as Cities graph using matplotlib.
        """

        software_as_cities_graph = nx.Graph()

        for cluster_label in cluster_centroid.keys():
            software_as_cities_graph.add_node(cluster_label)

        for route, route_value in cluster_to_route.items():

            software_as_cities_graph.add_edge(*route)

        return software_as_cities_graph



    def get_corpus(self):
        """ Get a list of identifiers of each file in a repo.
        """

        file_to_identifiers = {}
        for file_path in self.repo_files_path:

            print(file_path)

            try :
                with open(self.repo_folder + '\\' + file_path) as data_source:
                    ast_root = ast.parse(data_source.read())
                    
                identifiers = []

                for node in ast.walk(ast_root):
                    if isinstance(node, ast.Name):
                        identifiers.append(node.id)
                    elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
                        identifiers.append(node.name)

                file_to_identifiers[file_path] = identifiers

            except:
                print('Not .py file')
        
        return file_to_identifiers

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

            idf[word] = math.log(len(file_identifiers) / num_doc)

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

        norm_a = math.sqrt(norm_a)
        norm_b = math.sqrt(norm_b)

        return dot / (norm_a * norm_b)

    @staticmethod
    def split_sentence(word):
        """ Split a snake or camel case string into its composing words.
        """

        # Snake split
        splitted_snake_sentence = word.split('_')

        # camel_word = re.sub(r'_(.)', lambda m: m.group(1).upper(), word)

        splitted_sentence = []
        for snake_word in splitted_snake_sentence:
            camel_words = re.findall(r'.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', snake_word)
            for camel_word in camel_words:
                splitted_sentence.append(camel_word)

        return splitted_sentence


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

        

    def semantic_analysis(self):
        """ Runs a semantic analysis on a repo to get a distance matrix containing the cosine distance
        between each file.
        """

        file_to_identifiers = self.get_corpus()

        self.preprocess_words(file_to_identifiers)

        print(file_to_identifiers)

        voc_size, voc_to_index = self.compute_voc(file_to_identifiers)

        tf = self.compute_tf(voc_to_index, file_to_identifiers)
        idf = self.compute_idf(voc_to_index, file_to_identifiers)
        tf_idf = self.compute_tf_idf(voc_to_index, tf, idf)


        tf_idf_df = pd.DataFrame.from_dict(tf_idf, orient='index')

        distance_matrix = cosine_similarity(tf_idf_df)
        for i in range(len(distance_matrix)):
            distance_matrix[i][i] = 1
        distance_df = pd.DataFrame(distance_matrix, index=tf_idf_df.index, columns=tf_idf_df.index)


        correlated_files = set()
        for file_path in file_to_identifiers.keys():
            for file_path2 in file_to_identifiers.keys():

                if file_path != file_path2:
                    correlation = distance_df.loc[file_path, file_path2]
                    if correlation > 0 and correlation < 1:
                        files = sorted([file_path, file_path2])
                        correlated_files.add((files[0], files[1], correlation))

        correlated_files = sorted(list(correlated_files), key=lambda x: x[2], reverse=True)
        
        for i in range(50):
            print(correlated_files[i])

        print(distance_df)

        return distance_df

        # print(distance_df)

    def draw_map_semantic(self, name, load_existing=False, join_clusterless_samples=True, logical_roads=False):
        """ Same as draw_map() but with semantic analysis.
        """

        distance = self.semantic_analysis()

        # We need to run the analysis to get the dates
        df, commit_to_files, files_mod_dates = self.analyze_correlation(
                treecommit_analysis=False,
                commit_analysis=True,
                commit_lines_analysis=False,
                get_dataframe=True,
                get_commit_to_files_dict=True,
                get_dates=True)
        
        clusters, clusters_labels = self.cluster_dataframe(
                    distance,
                    method='HDBSCAN',
                    distance_matrix=True,
                    min_size=3,
                    max_eps=1,
                    join_clusterless_samples=join_clusterless_samples)


        with open("./clusters_semantic_{name}.txt", "wb") as fp:
            pickle.dump(clusters, fp)        
        
        df_reduced = self.dimensionality_reduction(distance, method='tSNE')

        cluster_centroid = self.find_centroids(df_reduced, clusters_labels)

        cluster_to_route = {}
        if logical_roads:
            cluster_to_route = self.find_routes(clusters, df)

        print(clusters)
        print(len(clusters))

        citiesData = []

        '''
        plt.scatter(df_reduced.iloc[:,0], df_reduced.iloc[:,1])
        plt.show()
        '''
        
        for key in clusters.keys():


            cityData = {}
            cityData['label'] = key
            cityData['centroid'] = {'x':cluster_centroid[key][0], 'y':cluster_centroid[key][1]}
            cityData['buildings'] = [{'height':10, 'fileName':name} for name in clusters[key]]


            citiesData.append(cityData)

        CommitGraphDrawer.CommitGraphDrawer.draw_threejs(citiesData, cluster_to_route, {}, files_mod_dates)

    

if __name__ == "__main__":
    

    url = "https://github.com/apache/airflow.git"

    print("Init CommitAnalyzer")
    ca = Analyzer(url)

    print("Draw map")
    ca.draw_map("flask", join_clusterless_samples=False)
    ca.draw_map_semantic("pydriller", join_clusterless_samples=False)
    ca.draw_hierarchical_edge_bundle("airflow", join_clusterless_samples=False)
    
  