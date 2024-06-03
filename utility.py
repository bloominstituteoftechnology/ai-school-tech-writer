import os
import base64
from datetime import datetime
from openai import OpenAI

def format_data_for_openai(diffs, commit_messages, changelog_contents):
    prompt = None

    # Combine the changes into a string with clear delineation.
    changes = '\n'.join([
        f'File: {file["filename"]}\n Diff: \n {file["patch"]}\n'
        for file in diffs
    ])

    # Combine all commit messages
    commit_messages = '\n'.join(commit_messages) + '\n\n'
    
    # Decode the README content
    changelog_file_content = base64.b64decode(changelog_contents.content).decode('utf-8')

    today = datetime.today().strftime('%Y-%m-%d')

    # Construct the prompt with clear instructions for the LLM.
    # track the prompt that is submitted
    # langfuse
    # create the dataset, then figure out what we want to use as the few-shot prompt
    prompt = (
        "Please review the following changes and commit messages from a Github pull request.\n"
        "code changes from pull request:\n"
        f"{changes}\n"
        "current changelog file content: \n"
        f"{changelog_file_content}\n"
        f"consider the code changes and commit messages, determine if the changlog readme needs to be updated.\n"
        f"if any yaml file in the /specs directory has been modified, add a new entry to the changelog CSV file.\n"
        f"Make sure to ensure to maintain its existing style and clarity. the changelog entry should contain today's date ({today}),\n"
        f"the endpoint or schema being changed, and briefly describe the changes.\n"
        f"Updated README:\n"
    )

    return prompt


def call_openai(prompt):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    try:
        # Construct the chat messages for the conversation
        messages = [
            {"role": "system", "content": "You are an AI trained to help with updating changelog files based on code changes."},
            {"role": "user", "content": prompt},
        ]
        
        # Make the API call to OpenAI chat interface
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
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


def update_existing_pr_with_changelog(repo, pull_request, updated_changelog, changelog_sha):
    """Update the existing PR with the updated changelog content."""
    commit_message = "Proposed changelog update based on recent code changes."

    # Update the changelog file on the existing PR branch
    repo.update_file("changelog.csv", commit_message, updated_changelog, changelog_sha, branch=pull_request.head.ref)

    # Add a comment to the PR to notify about the changelog update
    pull_request.create_issue_comment("Changelog file has been updated based on the recent code changes.")

    return pull_request # Return the pull request object if needed