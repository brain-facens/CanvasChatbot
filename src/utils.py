import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN_CANVAS")
canvas_api_url = os.getenv("CANVAS_API_URL")
headers = {"Authorization": f"Bearer {TOKEN}"}

class Request:
    def __init__(self):
        self.params = None
        self.course_id = None
        self.module_id = None

    def make_request(self, endpoint, params=None):
        url = f"{canvas_api_url}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro {response.status_code}: {response.text}")
            return None

    def list_courses(self, params=None):
        return self.make_request("/courses", params)

    def get_course_details(self, course_id, params=None):
        return self.make_request(f"/courses/{course_id}", params)

    def list_modules(self, course_id, params=None):
        return self.make_request(f"/courses/{course_id}/modules", params)

    def list_module_items(self, course_id, module_id, params=None):
        return self.make_request(f"/courses/{course_id}/modules/{module_id}/items", params)

# Função para criar um contexto inicial com a lista de cursos
def prepare_initial_prompt(courses, modules):
    course_list = "\n".join([f"- {course['name']}" for course in courses])
    modules_list = "\n".join([f"- {module['name']} (Curso: {module['course_name']})" for module in modules])

    return f"""
        Você é um assistente que ajuda estudantes a entenderem e gerenciarem seus cursos no Canvas LMS.
        Aqui estão os cursos disponíveis no Canvas LMS:
        {course_list}
        
        Aqui estão os módulos disponíveis nos cursos no Canvas LMS:
        {modules_list}
        
        **Nota importante:** Se você não encontrar a informação solicitada ou ela não existir, responda de forma clara que não encontrou a informação ou que ela não está disponível. 
        Como posso ajudá-lo hoje?
    """

def interact_with_chatbot(client, user_message, chat_history):
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
