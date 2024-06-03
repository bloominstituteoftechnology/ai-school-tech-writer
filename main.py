import os
from github import Github
from utility import *

def main():
    # Initialize GitHub API with token
    g = Github(os.getenv('GITHUB_TOKEN'))

    # Get the repo path and PR number from the environment variables
    repo_path = os.getenv('REPO_PATH')
    pull_request_number = int(os.getenv('PR_NUMBER'))
    
    # Get the repo object
    repo = g.get_repo(repo_path)

    # Fetch README content (assuming README.md)
    readme_content = repo.get_contents("README.md")
    changelog_contents = repo.get_contents("changelog.csv")
    print(changelog_contents)
    
    # Fetch pull request by number
    pull_request = repo.get_pull(pull_request_number)

    # Get the diffs of the pull request
    pull_request_diffs = [
        {
            "filename": file.filename,
            "patch": file.patch 
        } 
        for file in pull_request.get_files()
    ]

    # Get the commit messages associated with the pull request
    commit_messages = [commit.commit.message for commit in pull_request.get_commits()]

    # Format data for OpenAI prompt
    prompt = format_data_for_openai(pull_request_diffs, commit_messages, changelog_contents)

    # Call OpenAI to generate the updated README content
    updated_changelog = call_openai(prompt)

    # Update the existing PR with the code suggestion
    update_existing_pr_with_changelog(repo, pull_request, updated_changelog, changelog_contents.sha)


if __name__ == '__main__':
    main()