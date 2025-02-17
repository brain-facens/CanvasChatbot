import os
import json
from openai import OpenAI
import pgsql
from datetime import datetime
import logging
import requests

client = OpenAI()
logger = logging.getLogger(__name__)

user_name = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
rds_proxy_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
canvas_api_url = os.getenv("CANVAS_API_URL")
TOKEN = os.getenv("TOKEN_CANVAS")
headers = {"Authorization": f"Bearer {TOKEN}"}

def get_files(path="./scraping"):
    """ Obtém os arquivos do diretório fornecido. """
    if not os.path.exists(path):
        return []
    
    file_paths = []
    for f in os.listdir(path):
        full_path = os.path.join(path, f)
        if os.path.isfile(full_path):
            file_paths.append(full_path)
    return file_paths

def create_assistant():
    """ Cria um assistente OpenAI especializado na Facens. """
    description = "Você é um assistente especializado no uso de ferramentas online do Centro Universitário Facens."

    instructions = """
    Responda dúvidas sobre plataformas acadêmicas, sistemas de gestão, ambientes virtuais de aprendizagem 
    e demais serviços digitais oferecidos pela Facens. 
    Suas respostas devem ser baseadas exclusivamente nos documentos fornecidos. 
    Se não encontrar a informação necessária nos documentos, informe educadamente ao usuário que não pode ajudá-lo.
    """

    assistant = client.beta.assistants.create(
        name="Educational Assistant",
        description=description,
        instructions=instructions,
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
    )

    return assistant.id

def insert_chat_history(username: str, message: str, chat_response: str):
    date = datetime.now()
    try:
        with pgsql.Connection(
            address=(rds_proxy_host, 5432),
            user=user_name,
            password=password,
            database=db_name,
            tls=False,
        ) as db:
            insert_query = """
            INSERT INTO chat_history (username, message, chat_response, date)
            VALUES ($1, $2, $3, $4)
            """
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    message TEXT NOT NULL,
                    chat_response TEXT NOT NULL,
                    date TIMESTAMP NOT NULL
                );
                """
            )
            with db.prepare(insert_query) as insert_message:
                insert_message(username, message, chat_response, date)
                logger.info("Mensagem inserida com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inserir mensagem no banco: {str(e)}")

def process_files_and_run_assistant(assistant_id, query):
    """ Faz o upload dos arquivos e executa a pesquisa no assistente OpenAI. """
    
    # Criando um Vector Store
    vector_store = client.beta.vector_stores.create(name="Facens_VectorStore")
    
    file_paths = get_files()
    if not file_paths:
        return {"error": "Nenhum arquivo encontrado para upload."}
    
    files_streams = [open(file_path, "rb") for file_path in file_paths]

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id,
        files=files_streams 
    )

    if file_batch.status != "completed":
        return {"error": "Falha ao processar arquivos no Vector Store."}

    # Atualizando o assistente para usar o Vector Store
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    # Criando uma thread para a interação
    thread = client.beta.threads.create()

    # Enviando a consulta do usuário
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query,
    )

    # Executando a consulta
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Obtendo a resposta do assistente
    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
    
    if messages:
        response_content = messages[0].content[0].text
        return {"response": response_content.value}

    return {"error": "Nenhuma resposta encontrada."}

def make_request(endpoint, params=None):
    try:
        url = f"{canvas_api_url}{endpoint}"
        response = requests.get(
            url, 
            headers=headers, 
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse response: {str(e)}")
        return None

def get_username():
    user_data = make_request("/users/self")
    return user_data.get("name") if user_data else None

username = get_username()

def handler(event, context):
    """ Função principal para ser executada na AWS Lambda. """
    
    # Obtendo a consulta do evento (pode ser via API Gateway)
    body = json.loads(event.get("body", "{}"))
    query = body.get("query", "")

    if not query:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Nenhuma consulta fornecida."})
        }

    # ID do assistente, pode ser gerado uma vez e armazenado
    assistant_id = "asst_VWFEqFIlOolIqD5OxQZSbLT1"

    # Processa os arquivos e executa a pesquisa no assistente
    response_data = process_files_and_run_assistant(assistant_id, query)

    insert_chat_history(username=username, message=query, chat_response=response_data)

    return {
        "statusCode": 200,
        "body": json.dumps(response_data)
    }