import os
from dotenv import load_dotenv
from openai import OpenAI

from utils import *

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

if __name__ == "__main__":
    req = Request()

    courses = req.list_courses(params={"per_page": 5})
    all_modules = []

    for course in courses:
        course_modules = req.list_modules(course_id=course['id'], params={"per_page": 5})
        if course_modules:
            for module in course_modules:
                module["course_name"] = course["name"]  
                all_modules.append(module)

    if courses or all_modules:
        initial_prompt = prepare_initial_prompt(courses, all_modules)

        chat_history = [{"role": "system", "content": initial_prompt}]

        print("\nBem-vindo ao Chatbot do Canvas LMS!")
        print("Digite 'sair' para encerrar o chat.\n")

        while True:
            user_input = input("Você: ")
            if user_input.lower() in ["sair", "exit"]:
                print("Encerrando o chat. Até mais!")
                break

            if user_input.lower().startswith("módulos do curso"):
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
                response, chat_history = interact_with_chatbot(client, user_input, chat_history)
                print(f"Chatbot: {response}")
    else:
        print("Nenhum curso encontrado.")
