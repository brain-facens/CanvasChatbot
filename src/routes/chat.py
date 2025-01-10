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
async def chat(chat_data: Chat.chat_):
    req = Request()
    try:
        courses = req.get_courses()
        all_modules = req.get_all_modules(courses)
        user_message = chat_data.user_message

        if courses or all_modules:
            initial_prompt = prepare_initial_prompt(courses, all_modules)
            chat_history = [{"role": "system", "content": initial_prompt}]
            
            # Processar mensagem do usuário
            response, status_code = req.handle_user_message(user_message, courses, all_modules)
            if response:
                return JSONResponse(content=response, status_code=status_code)

            # Resposta do chatbot
            response, status_code = req.get_chatbot_response(client, user_message, chat_history)
            return JSONResponse(content=response, status_code=status_code)
        else:
            logger.info("Nenhum curso encontrado")
            return JSONResponse(content={"not found": "Nenhum curso encontrado"}, status_code=204)
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return JSONResponse(content={"error": f"Erro interno: {str(e)}"}, status_code=500)