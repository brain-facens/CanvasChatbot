import sys
import os
import traceback

sys.path.append(os.path.abspath("./package"))

import json
import logging
import pgsql
from datetime import datetime

import requests
import openai

user_name = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
rds_proxy_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN_CANVAS")
canvas_api_url = os.getenv("CANVAS_API_URL")
headers = {"Authorization": f"Bearer {TOKEN}"}

logger = logging.getLogger(__name__)


def get_stacktrace_str() -> str:
    ex_type, ex_value, ex_traceback = sys.exc_info()

    # Extract unformatter stack traces as tuples
    trace_back = traceback.extract_tb(ex_traceback)

    # Format stacktrace
    stack_trace = list()

    for trace in trace_back:
        stack_trace.append(
            "File : %s , Line : %d, Func.Name : %s, Message : %s"
            % (trace[0], trace[1], trace[2], trace[3])
        )

    return f"Exception type: {ex_type}, Exception Message: {ex_value}, stack trace: {stack_trace}"


def Insert_chat_history(username: str, message: str, chat_response: str, date: datetime):
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
                return
    except Exception as e:
        raise Exception(f"Error inserting document: {str(e)}")


def parse_date_friendly(date_string):
    """
    Converte uma data amigável, como '31 de janeiro', para o formato ISO (YYYY-MM-DD).
    Se a data não for válida, retorna None.

    Args:
        date_string (str): Data fornecida pelo usuário.

    Returns:
        str: Data em formato ISO, ou None se a conversão falhar.
    """
    try:
        # Mapeamento dos meses em português para números
        meses = {
            "janeiro": "01",
            "fevereiro": "02",
            "março": "03",
            "abril": "04",
            "maio": "05",
            "junho": "06",
            "julho": "07",
            "agosto": "08",
            "setembro": "09",
            "outubro": "10",
            "novembro": "11",
            "dezembro": "12",
        }

        # Divide a string de entrada
        partes = date_string.lower().strip().split(" de ")
        if len(partes) != 2:
            raise ValueError("Formato de data inválido")

        dia = partes[0]
        mes = meses.get(partes[1])
        if not dia.isdigit() or not mes:
            raise ValueError("Dia ou mês inválido")

        # Retorna a data no formato ISO
        ano_atual = datetime.now().year
        return f"{ano_atual}-{mes}-{int(dia):02d}"
    except Exception as e:
        logger.error(f"Erro ao interpretar a data '{date_string}': {str(e)}")
        return None


class Request:
    def __init__(self):
        self.params = None
        self.course_id = None
        self.module_id = None

    def make_request(self, endpoint, params=None):
        try:
            url = f"{canvas_api_url}{endpoint}"

            # Add timeout to prevent hanging
            response = requests.get(url, headers=headers, params=params, timeout=30)

            # Raise for bad status codes
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None
        # except ValueError as e:  # JSON decode error
        #     print(f"Failed to parse response: {str(e)}")
        #     return None

    def get_calendar(self):
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.get(
            f"{canvas_api_url}/calendar_events?start_date=2025-01-01&end_date=2025-12-31",
            headers=headers,
        )
        if response.status_code == 200:
            user_data = response.json()
            return user_data

    def get_calendar_events(self, title_filter=None, date_filter=None):
        try:
            events = self.get_calendar()

            # Filtra os eventos pelo título ou pela data, se fornecidos
            filtered_events = []
            for event in events:
                title_matches = (
                    title_filter.lower() in event["title"].lower()
                    if title_filter
                    else True
                )
                date_matches = date_filter in event["start_at"] if date_filter else True

                if title_matches and date_matches:
                    filtered_events.append(event)

            return filtered_events

        except Exception as e:
            logger.error(f"Erro ao buscar eventos do calendário: {str(e)}")
            return []

    def get_username(self):
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.get(f"{canvas_api_url}/users/self", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get("name")

    def list_courses(self, params=None):
        return self.make_request("/courses", params)

    def get_course_details(self, course_id, params=None):
        return self.make_request(f"/courses/{course_id}", params)

    def list_modules(self, course_id, params=None):
        return self.make_request(f"/courses/{course_id}/modules", params)

    def list_module_items(self, course_id, module_id, params=None):
        return self.make_request(
            f"/courses/{course_id}/modules/{module_id}/items", params
        )

    def get_courses(self):
        try:
            return self.list_courses(params={"per_page": 5})
        except Exception as e:
            print(f"Error fetching courses: {e}")
            return str(e)

    def get_all_modules(self, courses):
        all_modules = []
        for course in courses:
            course_modules = self.list_modules(
                course_id=course["id"], params={"per_page": 5}
            )
            if course_modules:
                for module in course_modules:
                    module["course_name"] = course["name"]
                    all_modules.append(module)
        return all_modules

    def handle_user_message(self, user_message, courses, all_modules):
        if user_message.lower().startswith("modulos do curso"):
            course_name = user_message[len("módulos do curso ") :].strip()
            selected_course = next(
                (
                    course
                    for course in courses
                    if course["name"].lower() == course_name.lower()
                ),
                None,
            )
            if selected_course:
                course_modules = [
                    module
                    for module in all_modules
                    if module["course_name"].lower() == course_name.lower()
                ]
                if course_modules:
                    modules_list = "\n".join(
                        [f"- {module['name']}" for module in course_modules]
                    )
                    logger.info(
                        f"Módulos do curso '{selected_course['name']}':\n{modules_list}"
                    )
                    return {
                        "message": f"Módulos do curso '{selected_course['name']}':\n{modules_list}"
                    }, 200
                else:
                    logger.info(
                        f"Nenhum módulo encontrado para o curso '{selected_course['name']}'."
                    )
                    return {
                        "not found": f"Nenhum módulo encontrado para o curso '{selected_course['name']}'."
                    }, 204
            else:
                logger.info("Curso não encontrado")
                return {"not found": "Curso não encontrado"}, 204
        current_datetime = datetime.now()
        username_logged = self.get_username()
        if user_message.lower().startswith("aulas no calendário"):
            # Extrai a parte do título e da data
            parts = user_message[len("aulas no calendário") :].strip().split(" no dia ")
            title_filter = parts[0].strip() if len(parts) > 0 else None
            date_friendly = parts[1].strip() if len(parts) > 1 else None

            # Converte a data amigável para o formato ISO
            date_filter = parse_date_friendly(date_friendly) if date_friendly else None

            # Busca eventos no calendário
            events = self.get_calendar_events(
                title_filter=title_filter, date_filter=date_filter
            )

            if events:
                # Formata a resposta com os eventos encontrados
                response = "\n".join(
                    [
                        f"- {event['title']} em {event['start_at']} (local: {event.get('location_name', 'não especificado')})"
                        for event in events
                    ]
                )
                Insert_chat_history(
                    username=username_logged,
                    message=user_message,
                    chat_response=f"Aulas encontradas:\n{response}",
                    date=current_datetime,
                )
                return {"message": f"Aulas encontradas:\n{response}"}, 200
            else:
                response = "Nenhuma aula encontrada com os critérios especificados."
                Insert_chat_history(
                    username=username_logged,
                    message=user_message,
                    chat_response=response,
                    date=current_datetime,
                )
                return {"not found": response}, 204
        return None, None


# Função para criar um contexto inicial com a lista de cursos
def prepare_initial_prompt(courses, modules):
    course_list = "\n".join([f"- {course['name']}" for course in courses])
    modules_list = "\n".join(
        [f"- {module['name']} (Curso: {module['course_name']})" for module in modules]
    )

    return f"""
        Você é um assistente que ajuda estudantes a entenderem e gerenciarem seus cursos no Canvas LMS.
        Aqui estão os cursos disponíveis no Canvas LMS:
        {course_list}
        
        Aqui estão os módulos disponíveis nos cursos no Canvas LMS:
        {modules_list}
        
        **Nota importante:** Se você não encontrar a informação solicitada ou ela não existir, responda de forma clara que não encontrou a informação ou que ela não está disponível. 
        Como posso ajudá-lo hoje?
    """


def interact_with_chatbot(user_message, chat_history):
    # Adicionar mensagem do usuário ao histórico
    chat_history.append({"role": "user", "content": user_message})

    # Fazer a chamada para a API da OpenAI
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=chat_history,
    )

    # Extrair a resposta
    assistant_message = (
        str(response.choices[0].message.content).encode().decode("utf-8")
    )

    # Adicionar a resposta ao histórico
    chat_history.append({"role": "assistant", "content": assistant_message})

    print(f"Resposta do assistente: {assistant_message}")
    print("Histórico do chat:")
    print(chat_history)

    return {"message": assistant_message}, 200


def build_response_v1(response, status_code):
    print("Sending back the response")
    print(json.dumps(response))

    generated_response = {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"} if response else {},
        "body": json.dumps(response) if response else "",
        "cookies": [],
        "isBase64Encoded": False,
    }

    print(json.dumps(generated_response))

    return generated_response


def handler(event, context):
    try:
        req = Request()
        courses = req.get_courses()
        all_modules = req.get_all_modules(courses)
        print(event)

        if not event["body"]:
            return build_response_v1(
                {"error": "Corpo da requisição não fornecido"}, 400
            )

        user_message = json.loads(event["body"]).get("user_message")

        if not user_message:
            return build_response_v1(
                {"error": "Mensagem do usuário não fornecida"}, 400
            )

        if courses or all_modules:
            initial_prompt = prepare_initial_prompt(courses, all_modules)
            chat_history = [{"role": "system", "content": initial_prompt}]

            # Processar mensagem do usuário
            response, status_code = req.handle_user_message(
                user_message, courses, all_modules
            )
            if response:
                return build_response_v1(response, status_code)

            # Resposta do chatbot
            response, status_code = interact_with_chatbot(user_message, chat_history)
            return build_response_v1(response, status_code)
        else:
            logger.info("Nenhum curso encontrado")
            return build_response_v1({"not found": "Nenhum curso encontrado"}, 404)
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        print(get_stacktrace_str())
        return build_response_v1({"error": f"Erro interno: {str(e)}"}, 500)
