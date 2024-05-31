import os
import base64
from openai import OpenAI

def format_data_for_openai(diffs, readme_content, commit_messages):
    prompt = None

    # Combine the changes into a string with clear delineation.
    changes = '\n'.join([
        f'File: {file["filename"]}\nDiff: \n{file["patch"]}\n'
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
    return prompt

def call_openai(prompt):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    try:
        # Construct the chat messages for the conversation
        messages = [
            {"role": "system", "content": "You are an AI trained to help with updating README files based on code changes."},
            {"role": "user", "content": prompt},
        ]
        
        # Make the API call to OpenAI chat interface
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )

        return response.choices[0].message.content 
    except Exception as e:
        print(f"Error making OpenAI API call: {e}")

def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    """Submit Updated README content as a PR in new branch."""
    commit_message = "Proposed README update based on recent code changes."

    # Create a new branch
    commit_sha = os.getenv('COMMIT_SHA')
    main_branch = repo.get_branch("main")
    new_branch_name = f"update-readme-{commit_sha[:7]}"
    new_branch = repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=main_branch.commit.sha)

    # Update the README on the new branch
    repo.update_file("README.md", commit_message, updated_readme, readme_sha, branch=new_branch_name)

    # Create a pull request    
    pr_title = "Update README based on recent changes"
    pr_body = "This PR proposes an update to the README based on recent code changes from the previous pull request."
    pull_request = repo.create_pull(title=pr_title, body=pr_body, head=new_branch_name, base="main")
    
    return pull_request # Return the pull request object if needed