from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging

from schemas import Chat
from utils import *

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/")
async def chat(
    chat_data: Chat.chat_
):
    req = Request()
    courses = req.list_courses(params={"per_page": 5})
    all_modules = []
    user_message = chat_data.user_message

    for course in courses:
        course_modules = req.list_modules(course_id=course['id'], params={"per_page": 5})
        if course_modules:
            for module in course_modules:
                module["course_name"] = course["name"]
                all_modules.append(module)

    if courses or all_modules:
        initial_prompt = prepare_initial_prompt(courses, all_modules)

        chat_history = [{"role": "system", "content": initial_prompt}]

        if user_message.lower().startswith("modulos do curso"):
            try:
                course_name = user_message[len("módulos do curso "):].strip()
                selected_course = next((course for course in courses if course["name"].lower() == course_name.lower()), None)
                if selected_course:
                    course_modules = [module for module in all_modules if module["course_name"].lower() == course_name.lower()]
                    if course_modules:
                        modules_list = "\n".join([f"- {module['name']}" for module in course_modules])
                        logger.info(f"Módulos do curso '{selected_course['name']}':\n{modules_list}")
                        content = {"message": f"Módulos do curso '{selected_course['name']}':\n{modules_list}"}
                        return JSONResponse(content=content, status_code=200)
                    else:
                        logger.info(f"Nenhum módulo encontrado para o curso '{selected_course['name']}'.")
                        content = {"not found": f"Nenhum módulo encontrado para o curso '{selected_course['name']}'."}
                        return JSONResponse(content = content, status_code=204)
                else:
                    content = {"not found": "Curso não encontrado"}
                    logger.info(f"Curso {selected_course} não encontrado")
                    return JSONResponse(content = content, status_code=204)
            except Exception as e:
                logger.error(f"{str(e)}")
                content = {"error": f"{str(e)}"}
                return JSONResponse(content=content, status_code=500)
        else:
            response, chat_history = interact_with_chatbot(client, user_message=user_message, chat_history=chat_history)
            logger.info(f"Chatbot: {response}")
            content = {"message": f"{response}"}
            return JSONResponse(content=content, status_code=200)
    else:
        content = {"not found": "Nenhum curso encontrado"}
        logger.info("Nenhum curso encontrado")
        return JSONResponse(content=content, status_code=204)