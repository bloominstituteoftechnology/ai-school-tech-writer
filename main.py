from github import Github
from constants import *
from utility import *
import json
import sys

def main():
    repo = g.get_repo(REPO_PATH)
    pull_request = repo.get_pull(PULL_REQUEST_NUMBER)
    pull_request_description_template = repo.get_contents(PULL_REQUEST_TEMPLATE_PATH)

    if not repo:
        raise Exception("Please set the REPO_PATH environment variable")
    if not pull_request:
        raise Exception("Please set the PR_NUMBER environment variable")
    if not pull_request_description_template:
        raise Exception("The pull request template has been moved")

    pull_request_diffs = [
        {
            "filename": file.filename,
            "patch": file.patch 
        }
        for file in pull_request.get_files()
    ]
    commit_messages = [commit.commit.message for commit in pull_request.get_commits()]

    json_pull_request_diffs = json.dumps(pull_request_diffs)

    prompt = format_data_for_prompt(pull_request_diffs, commit_messages, pull_request_description_template, diffs_context)
    pr_description = generate_pr_description(prompt)
    update_pr_description(repo, pr_description)

if __name__ == '__main__':
    main()
