import os
from typing_extensions import override
from openai import AssistantEventHandler, OpenAI

client = OpenAI()

def get_files(path = "./scraping"):
    files =  os.listdir(path)
    file_paths = []
    for f in files:
        if os.path.isfile(path + '/' + f):
            file_paths.append(path + '/' + f)
    return file_paths


def assistant(client):
    description = """
        Você é um assistente especializado no uso de ferramentas online do Centro Universitário Facens.
        """

    instruction = """
    Responda dúvidas sobre plataformas acadêmicas, sistemas de gestão, ambientes virtuais de aprendizagem 
    e demais serviços digitais oferecidos pela Facens. 
    Suas respostas devem ser baseadas exclusivamente nos documentos fornecidos. 
    Se não encontrar a informação necessária nos documentos, informe educadamente ao usuário que não pode ajudá-lo.
    """

    assistant = client.beta.assistants.create(
        name = "Educational Assistant",
        description = description,
        instructions = instruction,
        model = "gpt-4-turbo",
        tools = [{"type": "file_search"}],
    )

    print(assistant)

    return assistant


def data_batch_and_inference(assistant_id):
    vector_store = client.beta.vector_stores.create(name = "Facens")
    print(f"Vector Store ID = {vector_store.id}")
    
    file_paths = get_files()
    files_streams = [open(file_path, "rb") for file_path in file_paths]


    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id = vector_store.id,
        files = files_streams 
    )

    print(f"File Batch Status {file_batch.status}")

    assistant = client.beta.assistants.update(
        assistant_id=assistant_id, 
        tool_resources= {"file_search": {"vector_store_ids": [vector_store.id]}}, 
    )

    print("Assistant Updated with vector store!")

    thread = client.beta.threads.create()
    print(f"Your thread id is - {thread.id}\n\n")

    while True:
        text = input("O que deseja procurar?\n")

        message = client.beta.threads.messages.create(
            thread_id = thread.id,
            role = "user",
            content = text,
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id = thread.id,
            assistant_id = assistant.id 
        )

        messages = list(client.beta.threads.messages.list(thread_id = thread.id, run_id = run.id))
        message_content = messages[0].content[0].text
        print("Response: \n")
        print(f"{message_content.value}\n")

if __name__ == '__main__':
    #assistant = assistant(client)
    data_batch_and_inference("asst_9HF127l482zdHoWsbYcnJ38D")