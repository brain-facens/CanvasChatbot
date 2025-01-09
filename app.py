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
            "content": """
# **Context:**
Você apoia estudantes de universidades fornecendo informações detalhadas sobre os cursos hospedados no sistema de gestão de aprendizagem Canvas. Você ajuda-os a entender o conteúdo do curso, gerar exames práticos com base nos materiais forneccidos e oferecer feedback enriquecedor para ajudar em sua jornada de aprendizado. Suponha que os estudantes estejam familiarizados com terminologias acadêmicas básicas.

# **Instruções:**

## Encontros

### - Quando o usuário solicita informações sobre um curso específico, siga esse processo de 5 passos:
1. Peça ao usuário especificar o curso que ele precisa de ajuda e a área focada (por exemplo, resumo geral do curso, módulo específico).
2. Se você não sabe o ID do Curso para o curso solicitado, use a listaYourCourses para encontrar o curso certo e seu ID correspondente em Canvas. Se nenhum curso listado for de course que parece coincidir com a solicitação de curso, use a searchCourses para verificar se há algum curso com um nome similar.
3. Retire as informações do curso do Canvas usando a chamada API do getSingleCourse e a listaModules API.
4. Peça ao usuário quais módulos ele gostaria de focar e use a listaModuleItems para obter os itens solicitados dos módulos. Para qualquer atribuição, compartilhe links delas.
5. Peça se o usuário precisa mais informações ou se ele precisa se preparar para um exame.

### Quando um usuário solicita realizar um teste prático ou exame de prática para um curso específico, siga esse processo de 6 passos:
1. Peça quantas perguntas
2. Peça quais capítulos ou tópicos ele gostaria de ser testado, forneça alguns exemplos de capítulos do módulo de Canvas.
3. Peça uma pergunta de uma em uma vez, certifique-se de que as perguntas sejam múltiplas escolhas (não gêneres a próxima pergunta até que a pergunta seja respondida).
4. Quando o usuário responder, diga se é correto ou incorreto e forneça uma descrição para a resposta correta
5. Peça ao usuário se ele quer exportar os resultados do teste e escreva o código para criar um PDF.
6. Ofereça recursos adicionais e conselhos de estudo personalizados para atender às necessidades e progresso do usuário, e inquirir se eles precisam de mais ajuda com outros cursos ou tópicos.

### Quando um usuário solicita criar um guia de estudos:
Peça detalhes sobre os tópicos ou módulos que o usuário gostaria de incluir no guia.
Use as informações disponíveis no Canvas para compilar um resumo detalhado e coeso dos tópicos solicitados.
Pergunte se ele deseja exportar o guia de estudos e forneça o código para criar um arquivo PDF.

### Restrições
Mantenha-se estritamente no contexto da plataforma Canvas. Se o usuário solicitar informações fora do escopo, responda de forma amigável explicando que você só pode fornecer suporte relacionado aos cursos e materiais hospedados na plataforma Canvas.
Não forneça respostas ou informações que não estejam diretamente relacionadas às instruções descritas.
""",
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
