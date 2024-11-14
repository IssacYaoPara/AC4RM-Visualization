from openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from tenacity import retry, wait_random_exponential, stop_after_attempt
import os

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(5))
def chat_completion_request(client, messages, model="gpt-4o",
                            **kwargs):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

class Copilot:
    def __init__(self, key):
        reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
        docs = reader.load_data()
        embedding_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en"
        )
        self.index = VectorStoreIndex.from_documents(docs, embed_model = embedding_model,
                                                     show_progress=True)
        self.retriever = self.index.as_retriever(
                        similarity_top_k=3
                        )

        self.llm_client = OpenAI(api_key = key)
        
        self.system_prompt = """
            You are an expert on Li Auto's financial matrix and your job is to answer questions only related to Li Auto based on user's prompt. If the promt has nothing to do with Li Auto, you should not answer and ask the user to ask a related question instead.
        """

    def ask(self, question, messages):
        ### use the retriever to get the answer
        nodes = self.retriever.retrieve(question)
        ### make answer a string with "1. <>, 2. <>, 3. <>"
        retrieved_info = "\n".join([f"{i+1}. {node.text}" for i, node in enumerate(nodes)])
        

        processed_query_prompt = """
            The user is asking a question: {question}

            The retrived information is: {retrieved_info}

            Please answer questions follow the retrieved informations. If the question is not related to Li Auto, 
            please tell the user and ask for a question related to Li Auto.

            Please format your response in professional finance and banking format.
        """
        
        processed_query = processed_query_prompt.format(question=question, 
                                                        retrieved_info=retrieved_info)
        
        messages = [{"role": "system", "content": self.system_prompt}] + messages + [{"role": "user", "content": processed_query}]
        response = chat_completion_request(self.llm_client, 
                                           messages = messages, 
                                           stream=True)
        
        return retrieved_info, response

if __name__ == "__main__":
    ### get openai key from user input
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = input("Please enter your OpenAI API Key (or set it as an environment variable OPENAI_API_KEY): ")
    copilot = Copilot(key = openai_api_key)
    messages = []
    while True:
        question = input("Please ask a question: ")
        retrived_info, answer = copilot.ask(question, messages=messages)
        ### answer can be a generator or a string

        #print(retrived_info)
        if isinstance(answer, str):
            print(answer)
        else:
            answer_str = ""
            for chunk in answer:
                content = chunk.choices[0].delta.content
                if content:
                    answer_str += content
                    print(content, end="", flush=True)
            print()
            answer = answer_str

        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})