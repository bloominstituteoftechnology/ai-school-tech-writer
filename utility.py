import os
import base64
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.string import StrOutputParser

def format_data_for_openai(diffs, readme_content, commit_messages):
    prompt = None

    # Combine the changes into a string with clear delineation.
    changes = "\n".join(
        f'File: {diff["filename"]}\n{diff["patch"]}\n' for diff in diffs
    )

    # Combine all commit messages
    commit_messages = "\n".join(commit_messages)

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
        "Consider the code changes and commit messages, determine if the README needs to be updated. If so, edit the README, ensuring to maintain its existing style and clarity.\n"
        "Updated README:\n"
    )

    return prompt

def call_openai(prompt):
    client = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-3.5-turbo-0125")

    try:
        messages = [
            {"role": "system", "content": "You are an AI trained to help updating READMEs based on code changes and commit messages."},
            {"role": "user", "content": prompt},
        ]

        response = client.invoke(input=messages)
        parser = StrOutputParser()
        return parser.invoke(input=response)
    except Exception as e:
        print(f"Error making LLM: {e}")
        return "An error occurred while processing the request. Please try again later."

def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    commit_message = "AI COMMIT: Updated README based on code changes and commit messages"
    commit_sha = os.getenv("COMMIT_SHA")

    main_branch = repo.get_branch("main")
    new_branch_name = f'update-readme-{commit_sha[:7]}'
    new_branch = repo.create_git_ref(ref=f'refs/heads/{new_branch_name}', sha=main_branch.commit.sha)

    repo.update_file("README.md", commit_message, updated_readme, readme_sha, branch=new_branch_name)

    pr_title = "AI PR: Update README based on code changes and commit messages"
    pr_body = "This PR updates the README based on code changes and commit messages."
    pr = repo.create_pull(title=pr_title, body=pr_body, head=new_branch_name, base="main")

    return pr