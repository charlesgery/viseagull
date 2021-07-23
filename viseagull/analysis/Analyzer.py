from os import path
from atexit import register
from tempfile import TemporaryDirectory
from shutil import rmtree
from distutils.dir_util import copy_tree

from git import Repo
from pandas import DataFrame

from pydriller import Repository, Git
from tqdm import tqdm




class Analyzer:

    def __init__(self, url):
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

        self.url = url
        self.is_remote = False

        # Clone repo if necessary
        if self._is_remote_repository(url):
            self.repo_folder = self._clone_remote_repository(self._clone_folder(), url)
            self.is_remote = True
        else:
            self.repo_folder = self._clone_local_repository(self._clone_folder(), url)

        # Get a Repository object
        self.repository_mining = Repository(self.repo_folder, num_workers=1)

        # Get a Git object
        self.git_repo = Git(self.repo_folder)
        self.total_commits = self.git_repo.total_commits()

        # Get url to all files
        self.url_to_files = None
        if self.is_remote:
            active_branch = self.git_repo.repo.active_branch.name
            self.url_to_files = self.url[:-4] + '/blob/' + active_branch + '/'

        # Commits
        self.commits = []

        # Get list of files
        self.forbidden_file_extensions = ['.zip', '.gif', '.png']
        repo_files_paths = self.git_repo.files()
        self.path_prefix = path.commonpath(repo_files_paths)
        self.repo_files_path = []
        for file_path in repo_files_paths:
            _, file_extension = path.splitext(file_path)
            if file_extension not in self.forbidden_file_extensions:
                file_path = file_path[len(self.path_prefix)+1:]
                self.repo_files_path.append(file_path)
        
        # Find earlier names and paths of these files
        self.old_to_new_path = {}
        pbar = tqdm(total=self.total_commits)
        for commit in self.repository_mining.traverse_commits():
            self.commits.append(commit)
            for modification in commit.modified_files:
                if modification.old_path != modification.new_path and modification.old_path is not None:
                    self.old_to_new_path[modification.old_path] = modification.new_path
            pbar.update(1)
        pbar.close()

        self.df = None
        self.commit_to_files = {}
        self.files_modification_dates = {}

        self.distance_matrix = None

        self.couplings_type = None
        
        # Remove temp folder at end of execution
        register(self._cleanup)

    @staticmethod
    def _is_remote_repository(repo: str) -> bool:
        """ Checks wether or not repo is a local or remote path
        to a repo.
        """

        return repo.startswith("git@") or repo.startswith("https://")

    def _clone_remote_repository(self, path_to_folder: str, repo: str) -> str:
        """ Clones the remote repo to path_to_folder.
        """

        repo_folder = path.join(path_to_folder, self._get_repo_name_from_url(repo))
        Repo.clone_from(url=repo, to_path=repo_folder)

        return repo_folder

    def _clone_local_repository(self, path_to_tmp_folder: str, path_to_repo: str) -> str:
        """Clones a local repository to a temp folder
        """

        repo_folder = path.join(path_to_tmp_folder, self._get_repo_name_from_url(path_to_repo))
        copy_tree(path_to_repo, repo_folder)

        return repo_folder
    
    def _clone_folder(self) -> str:
        """ Create and returns a temporary folder.
        """

        self._tmp_dir = TemporaryDirectory()
        clone_folder = self._tmp_dir.name

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
                rmtree(self._tmp_dir.name, ignore_errors=True)

    def run_general_analysis(self,
            get_logical_couplings_df=False,
            get_commit_to_files=False,
            get_dates=False):

        # Initialize variables to create a dataframe containing the commits
        files_commits = {}
        columns = []

        for i, commit in enumerate(self.commits):

            columns.append(commit.hash)

            modified_files = []
            for modification in commit.modified_files:

                current_path = self.get_current_path(modification.new_path)

                if current_path is not None:

                    modified_files.append(current_path)

                    # Update files_modification_dates
                    if get_dates:
                        self.update_files_modification_dates(commit, current_path)

                    # Updating dataframe data
                    if get_logical_couplings_df:
                        self.update_logical_couplings_df_data(current_path, files_commits, i)

            if get_commit_to_files:
                self.commit_to_files[commit.hash] = modified_files

        # Create dataframe
        if get_logical_couplings_df:
            self.create_logical_couplings_df(files_commits, i, columns)

    def update_files_modification_dates(self, commit, current_path):

        commit_date = commit.committer_date
        if current_path not in self.files_modification_dates:
            self.files_modification_dates[current_path] = {'creation_date': commit_date, 'last_modification': commit_date}
        else:
            self.files_modification_dates[current_path]['last_modification'] = commit_date

    def update_logical_couplings_df_data(self, current_path, files_commits, i):

        if current_path in files_commits:
            while len(files_commits[current_path]) < i:
                files_commits[current_path].append(0)
            files_commits[current_path].append(1)
        
        else:
            files_commits[current_path] = [0 for _ in range(i)]
            files_commits[current_path].append(1)

    def create_logical_couplings_df(self, files_commits, i, columns):
        
        dataframe_list = []
        index = []
        for key in files_commits.keys():

            if len(files_commits[key]) < i+1:

                while len(files_commits[key]) < i+1:
                        files_commits[key].append(0)

            index.append(key)
            dataframe_list.append(files_commits[key])
        
        self.df = DataFrame(dataframe_list, index=index, columns=columns)

    def get_current_path(self, path):
        if path in self.repo_files_path:
            current_path = path
        else:
            current_path = self.retrieve_current_path(path)

        return current_path

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

    def compute_couplings(self):
        """ Updates Analysis object data with the results of a couplings analysis.
        """
        pass

    def get_distance_matrix(self):
        pass

