import os
import base64
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.string import StrOutputParser

def format_data_for_openai(diffs, readme_content, commit_messages):

    # Combine the changes into a string with clear delineation.

    changes = "\n".join([
        f"File: {file["filename"]}\nDiff: \n{file["patch"]}\n"
        for file in diffs
    ])+"\n\n"

    # Combine all commit messages
    commit_messages = "\n".join(commit_messages, "\n")+"\n\n"

    # Decode the README content
    readme_content = base64.b64decode(readme_content).decode("utf-8")

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        "Please review the following code changes and commit messages from a GitHub pull request:\n"
        "Code changes from Pull Request:\n"
        f"{changes}\n"
        "Commit messages:\n"
        f"{commit_messages}"
        "Here is the current README file content:\n"
        f"{readme_content}\n"
        "Consider the code changes and commit messages, determine if the README needs to be updated. If so, edit the README, ensuring to maintain its existing style and clarity.\n"
        "Updated README:\n"
    )
    return prompt

def call_openai(prompt):
    client = ChatOpenAI(api_key = os.getenv("OPENAI_API_KEY"), model="gpt-3.5-turbo")
    messages = [
        {"role": "system", "content": "You are a developer trained in updating README files from pull request messages"},
        {"role": "user", "content": prompt}
    ]
    try:
        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)
        return content
    except Exception as e:
        return f"An error occurred: {e}"

def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    commit_message = "Update README based on Agent feedback"

    commit_sha = os.getenv("GITHUB_SHA")
    main_branch = repo.get_branch("main")
    new_branch_name = f'update-readme-{commit_sha[:7]}'
    new_branch = repo.create_git_ref(ref=f'refs/heads/{new_branch_name}', sha=main_branch.commit.sha)

    repo.update_file(
        path="README.md",
        message=commit_message,
        content=updated_readme,
        sha=readme_sha,
        branch=new_branch_name
    )

    pr_title = "AI PR: Update README based on Agent feedback"
    pr_body = "This PR updates the README based on feedback from an AI agent."
    pr = repo.create_pull(title=pr_title, body=pr_body, base="main", head=new_branch_name)

    return pr.html_url
