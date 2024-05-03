import os
import base64
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.string import StrOutputParser

def format_data_for_openai(diffs, readme_content, commit_messages):
    prompt = None

    # Combine the changes into a string with clear delineation.
    changes = '\n'.join([
        f'file: {file["filename"]}\nDiff: \n{file["patch"]}\n'
        for file in diffs
    ])

    # Combine all commit messages
    commit_messages = '\n'.join(commit_messages) + '\n\n'

    # Decode the README content
    readme_content = base64.b64decode(readme_content.content).decode('utf-8')

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
    print(prompt)

    return prompt

def call_openai(prompt):
    client = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
    try:
        messages = [
            {
                "role": "system", "content": "You are an AI assistant trained to help with updating README files based on commit meessages and code files."
            }, 
            {
                "role": "user", "content": prompt
            }
        ]
        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)
        return content
    except Exception as e:
        print(f"Error making LLM call: {e}")


def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    commit_message = "AI COMMIT: Update README based on PR changes"
    commit_sha = os.getenv('COMMIT_SHA')
    main_branch = repo.get_branch('main')
    new_branch_name = f'update-readme-{commit_sha[:7]}'
    new_branch = repo.create_git_ref(f'refs/heads/{new_branch_name}', sha=main_branch.commit.sha)

    
    repo.update_file("README.md", commit_message, updated_readme, readme_sha, branch=new_branch_name)
    pr_title = "AI PR: Update README based on PR changes"
    pr_body = "This is an AI PR. Please review the README"
    pull_request = repo.create_pull(title=pr_title, body=pr_body, head=new_branch_name, base="main")

    return pull_request