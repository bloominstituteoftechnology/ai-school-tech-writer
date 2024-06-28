import os
import base64
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

def format_data_for_openai(diffs, readme_content, commit_messages):
    # prompt = None

    chnages = "\n".join(f"File: {file["filename"]}\nDiff:\n{file["patch"]}\n" for file in diffs)

    # Combine the changes into a string with clear delineation.
    commit_messages = "\n".join(commit_messages)+"\n\n"

    # Combine all commit messages
    

    # Decode the README content
    readme_content = base64.b64decode(readme_content.content).decode("utf-8")

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        "Please review the following changes and and commit messages from Github request:\n"
        "Code changes from Pull Request:\n"
        f"{changes}\n"
        "Commit messags:\n"
        f"{commit_messages}\n"
        "Here is the current README file content:\n"
        f"{readme_content}\n"
        "Consider the code changes and commit messages, determine if the README needs to be updated. If sok edit the README, ensuring to maintain its existing style and clarity."

    )

    return prompt

def call_openai(prompt):
    client = ChatOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    try:
        messages = [
            {"role": "system", "content": "You are an AI trained to help with updating README files based on code changes and commit messages."},
            {"role": "user", "content": prompt}
        ]

        #invoke
        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)
    except Exception as e:
        print(f"An error occurred making OpenAI API call: {e}")

def update_readme_and_create_pr(repo, updated_readme, readme_sha):
    pass