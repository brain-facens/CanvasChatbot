import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da API do Canvas LMS
TOKEN = os.getenv("TOKEN_CANVAS")
canvas_api_url = "https://facens.test.instructure.com/api/v1"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Configuração da API da OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Função genérica para requisições à API do Canvas
def make_request(endpoint, params=None):
    url = f"{canvas_api_url}{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro {response.status_code}: {response.text}")
        return None

# Funções para obter dados do Canvas LMS
def list_courses(params=None):
    return make_request("/courses", params)

def get_course_details(course_id, params=None):
    return make_request(f"/courses/{course_id}", params)

def list_modules(course_id, params=None):
    return make_request(f"/courses/{course_id}/modules", params)

def list_module_items(course_id, module_id, params=None):
    return make_request(f"/courses/{course_id}/modules/{module_id}/items", params)

# Função para criar um contexto inicial com a lista de cursos
def prepare_initial_prompt(courses):
    course_list = "\n".join([f"- {course['id']}: {course['name']}" for course in courses])
    return f"""
Você é um assistente que ajuda estudantes a entenderem e gerenciarem seus cursos no Canvas LMS.
Aqui estão os cursos disponíveis no Canvas LMS:
{course_list}

**Nota importante:** Se você não encontrar a informação solicitada ou ela não existir, responda de forma clara que não encontrou a informação ou que ela não está disponível. Não forneça respostas genéricas.
Como posso ajudá-lo hoje?
"""

# Função para interagir com o chatbot
def interact_with_chatbot(user_message, chat_history):
    # Adicionar mensagem do usuário ao histórico
    chat_history.append({"role": "user", "content": user_message})

    # Fazer a chamada para a API da OpenAI
    response = client.chat.completions.create(
        model="gpt-4",
        messages=chat_history,
    )
    
    # Extrair a resposta
    assistant_message = response.choices[0].message.content

    # Adicionar a resposta ao histórico
    chat_history.append({"role": "assistant", "content": assistant_message})

    return assistant_message, chat_history

# Loop principal do chatbot
if __name__ == "__main__":
    # Obter lista de cursos
    courses = list_courses(params={"per_page": 5})
    if courses:
        # Criar o prompt inicial do sistema
        initial_prompt = prepare_initial_prompt(courses)

        # Criar o histórico inicial do chat
        chat_history = [{"role": "system", "content": initial_prompt}]

        # Mostrar cursos disponíveis no console
        print("Lista de Cursos Disponíveis:")
        for course in courses:
            print(f"- {course['id']}: {course['name']}")
        
        # Iniciar interação com o chatbot
        print("\nBem-vindo ao Chatbot do Canvas LMS!")
        print("Digite 'sair' para encerrar o chat.\n")

        while True:
            user_input = input("Você: ")
            if user_input.lower() in ["sair", "exit"]:
                print("Encerrando o chat. Até mais!")
                break

            # Interagir com o chatbot
            response, chat_history = interact_with_chatbot(user_input, chat_history)
            print(f"Chatbot: {response}")
    else:
        print("Nenhum curso encontrado.")
