import streamlit as st
from openai import OpenAI
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN_CANVAS")
canvas_api_url = os.getenv("CANVAS_API_URL")
headers = {"Authorization": f"Bearer {TOKEN}"}

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("Canvas Chatbot")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if not any(msg["role"] == "system" for msg in st.session_state["messages"]):
    st.session_state["messages"].insert(
        0,
        {
            "role": "system",
            "content": "Você é um assistente útil que responde todas as perguntas em português do Brasil. Seja claro e educado.",
        },
    )

def get_canvas_data(endpoint):
    try:
        response = requests.get(f"{canvas_api_url}{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

for message in st.session_state["messages"]:
    if message["role"] != "system":  # Ignorar mensagens do sistema
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Pergunte algo sobre o Canvas LMS"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if "cursos" in prompt.lower():
        canvas_response = get_canvas_data("/courses")
        if "error" not in canvas_response:
            courses = [course["name"] for course in canvas_response]
            content = f"Os cursos disponíveis são:\n- " + "\n- ".join(courses)
        else:
            content = f"Erro ao consultar cursos: {canvas_response['error']}"
    else:
        content = ""
        for chunk in client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["messages"]
            ],
            stream=True,
        ):
            if chunk.choices and chunk.choices[0].delta and hasattr(chunk.choices[0].delta, "content"):
                content_chunk = chunk.choices[0].delta.content
                if content_chunk:
                    content += content_chunk

    with st.chat_message("assistant"):
        st.markdown(content)

    st.session_state["messages"].append({"role": "assistant", "content": content})