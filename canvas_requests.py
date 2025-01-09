import os
from dotenv import load_dotenv
from openai import OpenAI

from utils import *

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da API da OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Loop principal do chatbot
if __name__ == "__main__":
    # Instanciar o objeto Request para interagir com a API do Canvas
    req = Request()

    # Obter lista de cursos
    courses = req.list_courses(params={"per_page": 5})
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
            response, chat_history = interact_with_chatbot(client, user_input, chat_history)
            print(f"Chatbot: {response}")
    else:
        print("Nenhum curso encontrado.")
