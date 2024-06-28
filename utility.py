import os
import base64
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

def format_data_for_openai(diffs, readme_content, commit_messages):
    # Combine the changes into a string with clear delineation.
    changes = "\n".join([f"File: {file["filename"]}\nDiff:\n{file["patch"]}\n" for file in diffs])    
    
    # Combine all commit messages
    commit_messages = "\n".join(commit_messages) + "\n\n"
    # Decode the README content
    readme_content = base64.b64decode(readme_content.content).decode('utf-8')
    # Construct the prompt with clear instructions for the LLM.
    prompt = {
        "Please review the following code changes and cmmit messages from a Github Pull Request:\n"
        "Code changes from Pull Request:\n"
        f"{changes}\n"
        "Commit messages from Pull Request:\n"
        f"{commit_messages}\n"
        "The current README.md file is:\n"
        f"{readme_content}\n"
        "Consider the code changes and commit messages, detrmine if the README needs to be updated. If so, edit the README, ensuring to maintain its existing style and clarity\n"
        
        "Updated README.md:\n"
        
    }
    return prompt

def call_openai(prompt):
    client = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    try:
        messages = [
            {"role": "system", "content": "You are an AI trained to help with updating README files based on code changes."},
            {"role": "user", "content": prompt}
        ]
    #invoke
        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)
        return content
    except Exception as e:
        print(f"Error: {e}")
    
    pass

def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    """
    Submit Updated README content as a PR in a new branch
    """

    commit_message = "Proposed README update based on recent code changes"
    main_branch = repo.get_branch("main")
    new_branch_name = f"update-readme-{readme_sha[:10]}"
    new_branch = repo.create_git_ref(
        ref=f"refs/heads/{new_branch_name}", sha=main_branch.commit.sha
    )

    # Update the README file
    repo.update_file(
        path="README.md",
        message=commit_message,
        content=updated_readme,
        sha=readme_sha,
        branch=new_branch_name,
    )

    # Create a PR for this document anad stuff
    pr_title = "Update README based on recent changes"
    br_body = "This PR proposes an update to the README based on recent code changes. Please review and merge if appropriate."
    pull_request = repo.create_pull(
        title=pr_title, body=br_body, head=new_branch_name, base="main"
    )

    return pull_request