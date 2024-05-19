from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers.string import StrOutputParser
from langchain_community.document_loaders import DirectoryLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from .constants import *
from typing import List
import base64
import json
import os

def load_documents() -> List[str]:
    """Loads PDF documents to be used in embeddings in a vector store"""
    loader = DirectoryLoader("./", glob="*.*")
    raw_documents = loader.load()

    return raw_documents

def get_split_documents(raw_documents: List[str]) -> List[str]:
    """Chunks codebase documents to be used in embeddings in a vector store"""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_documents = text_splitter.split_documents(raw_documents)

    return split_documents

def embed_documents(index_name: str) -> None:
    """Embeds chunked documents in Pinecone's vector store after creating a new index"""
    raw_documents = load_documents()
    split_documents = get_split_documents(raw_documents)
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)

    pc = Pinecone(api_key=PINECONE_API_KEY)
    pc.create_index(
        name=index_name,
        dimension=3072,
        metric="cosine", 
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        ),
    )

    PineconeVectorStore.from_documents(
        documents=split_documents,
        embedding=embeddings,
        index_name=index_name
    )

def get_embeddings_for_diffs(index_name: str, diffs: List[str]) -> List[str]:
    """Takes a list of diffs from a PR, stringifies them, and does embedded search"""
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    document_vectorstore = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )

    retriever = document_vectorstore.as_retriever()

    json_pull_request_diffs = json.dumps(diffs)

    return retriever.invoke(json_pull_request_diffs)

def delete_embeddings_for_codebase(index_name: List[str]) -> str:
    """Deletes an index from the Pinecone account"""
    pc = Pinecone(api_key=PINECONE_API_KEY)
    pc.delete_index(index_name)

def format_data_for_prompt(diffs, commit_messages, codebase_context, pull_request_description_template):
    """Formats contextual data and generates the prompt with it, including for system data"""

    # Combine the changes into a string with clear delineation.
    changes = '\n'.join([
        f'File: {file["filename"]}\nDiff: \n{file["patch"]}\n'
        for file in diffs
    ])

    # Combine all commit messages
    commit_messages = '\n'.join(commit_messages) + '\n\n'

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        "Please review the following code changes and commit messages from a GitHub pull request:\n"
        "Code changes from Pull Request:\n"
        f"{changes}\n"
        "Commit messages:\n"
        f"{commit_messages}"
        "Here's context from existing files in the codebase:"
        f"{codebase_context}"
        "Consider the code changes, commit messages, and codebase context given above, write a pull request description. Be concise with no yapping, and just summarize bullet points of what's changed instead of listing all file paths and what changed inside each of them. Keep all of this relatively high level.\n"
        "Here is the markdown pull request template. Only use the sections in this content and do not add any others. Do not add a new Pull Request Description header. Keep the markdown heirarchy as it is in the content you've been given, and don't add any other headers. Do not add a new title for the template.\n"
        f"{pull_request_description_template}\n"
        "Pull request description:\n"
    )

    return prompt

def generate_pr_description(prompt: str) -> str:
    """Uses a model (currently OpenAI) to generate a new pull request description"""
    client = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")

    try:
        messages = [
            {"role": "system", "content": "You are an expert code reviewer tasked with summarizing all changes in a pull request and writing an incredible description for it."},
            {"role": "user", "content": prompt}
        ]

        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)

        return content
    except Exception as e:
        print(f'Error making LLM call: {e}')

def update_pr_description(repo: Github.Repository.Repository, pull_request_number: int, pull_request_description: str) -> None:
    """Updates a given pull request at a given repo with a new description"""
    pr = repo.get_pull(pull_request_number)
    pr.edit(body=pull_request_description)