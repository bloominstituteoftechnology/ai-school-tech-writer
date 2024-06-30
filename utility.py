import os
import base64
from github import Github
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

def format_data_for_openai(diffs, readme_content, commit_messages):
    # Combine the changes into a string with clear delineation.
    changes = "\n".join(
        [f'File: {file["filename"]}\nDiff: \n{file["patch"]}\n' for file in diffs]
    )

    # Combine all commit messages
    commit_messages = "\n".join(commit_messages) + "\n\n"

    # Decode the README content
    readme_content = base64.b64decode(readme_content.content).decode("utf-8")

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        "Please review the following code changes and commit messages from a GitHub pull request:\n"
        "Code changes from Pull Request:\n"
        f"{changes}\n"
        "Commit messages:\n"
        f"{commit_messages}"
        "Here is the current README file content:\n"
        f"{readme_content}\n"
        "Consider the code changes from the Pull Request (including changes in docstrings and other metadata), and the commit messages. Determine if the README needs to be updated. If so, edit the README, ensuring to maintain its existing style and clarity.\n"
        "Updated README:\n"
    )

    return prompt

def call_openai(prompt):
    client = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        messages = [
            {
                "role": "system",
                "content": "You are an AI trained to help with updating README files based on code changes.",
            },
            {"role": "user", "content": prompt},
        ]

        # Call OpenAI
        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)

        return content
    except Exception as e:
        print(f"Error making OpenAI API call: {e}")
        return None

def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    """
    Submit Updated README content as a PR in a new branch
    """
    commit_message = "Proposed README update based on recent code changes"
    main_branch = repo.get_branch("main")
    new_branch_name = f"update-readme-{readme_sha[:10]}"

    try:
        # Check if the branch already exists
        repo.get_git_ref(f"heads/{new_branch_name}")
        print(f"Branch {new_branch_name} already exists.")
    except GithubException as e:
        if e.status == 404:
            # Branch does not exist, create it
            repo.create_git_ref(
                ref=f"refs/heads/{new_branch_name}", sha=main_branch.commit.sha
            )
        else:
            raise e

    # Update the README file
    repo.update_file(
        path="README.md",
        message=commit_message,
        content=updated_readme,
        sha=readme_sha,
        branch=new_branch_name,
    )

    # Create a PR
    pr_title = "Update README based on recent changes"
    pr_body = "This PR proposes an update to the README based on recent code changes. Please review and merge if appropriate."
    pull_request = repo.create_pull(
        title=pr_title, body=pr_body, head=new_branch_name, base="main"
    )

    return pull_request

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
    prompt = format_data_for_openai(pull_request_diffs, readme_content, commit_messages)

    # Call OpenAI to generate the updated README content
    updated_readme = call_openai(prompt)

    if updated_readme:
        # Create PR for Updated PR
        pr = update_readme_and_create_pr(repo, updated_readme, readme_content.sha)
        print(f"Created PR: {pr.html_url}")
    else:
        print("Failed to generate updated README content.")

if __name__ == '__main__':
    main()
