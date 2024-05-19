from github import Github
from src.constants import *
from src.utility import *
import random
import json
import sys

def main():
    # Initialize PyGithub
    g = Github(GITHUB_API_KEY)

    # Fetch repository
    repo = g.get_repo(REPO_PATH)
    pull_request = repo.get_pull(PULL_REQUEST_NUMBER)

    # Get pull request template content
    root_dir = os.getcwd()
    file_path = os.path.join(root_dir, PULL_REQUEST_TEMPLATE_PATH)
    with open(file_path, "r") as file:
        pull_request_description_template = file.read()

    # Get all current pull request diffs
    pull_request_diffs = [
        {
            "filename": file.filename,
            "patch": file.patch 
        }
        for file in pull_request.get_files()
    ]
    
    # Get all current pull request commit messages and convert to JSON
    commit_messages = [commit.commit.message for commit in pull_request.get_commits()]
    json_pull_request_diffs = json.dumps(pull_request_diffs)

    # Do embeddings on codebase
    current_index_name = "autopr"
    embed_documents(current_index_name)

    # Search embeddings
    codebase_context = get_embeddings_for_diffs(current_index_name, pull_request_diffs)
    print(codebase_context)

    # Delete index and codebase embeddings
    delete_embeddings_for_codebase(current_index_name)

    # Build prompt
    prompt = format_data_for_prompt(
        pull_request_diffs,
        commit_messages,
        codebase_context,
        pull_request_description_template,
    )

    # Call model for PR description
    pr_description = generate_pr_description(prompt)

    # Update PR description
    update_pr_description(repo, PULL_REQUEST_NUMBER, pr_description)

if __name__ == '__main__':
    main()
