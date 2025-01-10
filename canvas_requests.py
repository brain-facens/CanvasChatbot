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
    all_modules = []

    # Obter módulos de cada curso
    for course in courses:
        course_modules = req.list_modules(course_id=course['id'], params={"per_page": 5})
        if course_modules:
            for module in course_modules:
                module["course_name"] = course["name"]  # Adicionar nome do curso ao módulo
                all_modules.append(module)

    if courses or all_modules:
        # Criar o prompt inicial do sistema sem exibir IDs para o usuário
        initial_prompt = prepare_initial_prompt(courses, all_modules)

        # Criar o histórico inicial do chat
        chat_history = [{"role": "system", "content": initial_prompt}]

        # Iniciar interação com o chatbot
        print("\nBem-vindo ao Chatbot do Canvas LMS!")
        print("Digite 'sair' para encerrar o chat.\n")

        while True:
            user_input = input("Você: ")
            if user_input.lower() in ["sair", "exit"]:
                print("Encerrando o chat. Até mais!")
                break

            if user_input.lower().startswith("módulos do curso"):
                # Extrair o nome do curso da entrada do usuário
                try:
                    course_name = user_input[len("módulos do curso "):].strip()
                    selected_course = next((course for course in courses if course["name"].lower() == course_name.lower()), None)
                    if selected_course:
                        course_modules = [module for module in all_modules if module["course_name"].lower() == course_name.lower()]
                        if course_modules:
                            modules_list = "\n".join([f"- {module['name']}" for module in course_modules])
                            print(f"Módulos do curso '{selected_course['name']}':\n{modules_list}")
                        else:
                            print(f"Nenhum módulo encontrado para o curso '{selected_course['name']}'.")
                    else:
                        print("Curso não encontrado.")
                except ValueError:
                    print("Comando inválido. Use: 'módulos do curso <nome do curso>'")
            else:
                # Interagir com o chatbot
                response, chat_history = interact_with_chatbot(client, user_input, chat_history)
                print(f"Chatbot: {response}")
    else:
        print("Nenhum curso encontrado.")
