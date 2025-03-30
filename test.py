import argparse
from langchain_community.document_loaders import YoutubeLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS


import os
import constants

os.environ["OPENAI_API_KEY"] = constants.APIKEY

def load_and_vectorize(youtube_url):
    loader = YoutubeLoader.from_youtube_url(youtube_url, add_video_info=False)
    docs = loader.load()
    docs = loader.load()
    embeddings = OpenAIEmbeddings()  # create an instance of the embedding model
    # Specify FAISS as the vectorstore class for persistent storage
    index = VectorstoreIndexCreator(embedding=embeddings, vectorstore_cls=FAISS).from_documents(docs)
    return index

def main():
    parser = argparse.ArgumentParser(description="Query a YouTube video")
    parser.add_argument("-url", type=str, help="The YouTube URL from the video")
    args = parser.parse_args()

    youtube_url = args.url
    print("YouTube URL:", youtube_url)
    index = load_and_vectorize(youtube_url)

    # Create an LLM instance
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.6)

    # Convert the FAISS vectorstore index into a retriever and build a QA chain
    retriever = index.vectorstore.as_retriever()
    qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

    query = input("What is your question? (enter 'quit' or 'q' to exit): ")
    while query.lower() not in ["quit", "q"]:
        # Using invoke as recommended instead of run
        response = qa_chain.invoke({"query": query})
        print("Answer:", response)
        query = input("What is your question? (enter 'quit' or 'q' to exit): ")

if __name__ == "__main__":
    main()
