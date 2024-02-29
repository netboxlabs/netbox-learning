import logging
from github.GithubException import BadCredentialsException, GithubException, UnknownObjectException
from github import Github, Auth, InputGitTreeElement

class GitHubRepoHelper:

    github = None
    logger = None
    repo = None
    
    __instance = None

    def __init__(self, auth_token, gh_org, gh_repo_name):
        logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.DEBUG)
        
        self.logger = logging.getLogger(__name__)
        
        try:
            auth = Auth.Token(auth_token)
            self.github = Github(auth=auth)

            repo_full_path = f"{gh_org}/{gh_repo_name}"
            self.repo = self.github.get_repo(repo_full_path)
            
            self.logger.info(f"Succefully connected to {repo_full_path}")
            
        except BadCredentialsException as e:
            self.logger.critical(f"Could not auth against GitHub. Exception: {e}")
        except GithubException as e:
            self.logger.critical(f"Error interacting with GitHub. Exception: {e}")
        except Exception as e:
            self.logger.debug(f"Caught exception of type {type(e)}. Description: {e}")
            return None
        
    # Functions
    def write_config_to_gh(self, file_path, file_name, file_contents, commit_message):
        commit = None

        try:
            # Create a blob for each file
            facts_blob = self.repo.create_git_blob(content=file_contents, encoding='utf-8')

            # Get the GH tree for the current HEAD
            head_sha = self.repo.get_branch('main').commit.sha
            base_tree = self.repo.get_git_tree(sha=head_sha)
            
            # Create a new tree with the blobs
            new_tree = self.repo.create_git_tree(
                tree=[
                    InputGitTreeElement(
                        path=f"{file_path}/{file_name}",
                        mode="100644",
                        type="blob",
                        sha=facts_blob.sha,
                    ),
                ],
                base_tree=base_tree
            )

            parent = self.repo.get_git_commit(sha=head_sha)
            commit = self.repo.create_git_commit(commit_message, new_tree, [parent])
            master_ref = self.repo.get_git_ref('heads/main')
            master_ref.edit(sha=commit.sha)
            return commit

        except Exception as e:
            print(e)