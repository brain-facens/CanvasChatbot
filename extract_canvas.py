import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN_CANVAS")
canvas_api_url = os.getenv("CANVAS_API_URL")
headers = {"Authorization": f"Bearer {TOKEN}"}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_request(endpoint, params=None):
    try:
        url = f"{canvas_api_url}{endpoint}"
        response = requests.get(
            url, 
            headers=headers, 
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse response: {str(e)}")
        return None

def get_calendar():
    return make_request("/api/v1/calendar_events", {"start_date": "2025-01-01", "end_date": "2025-12-31"})

def get_calendar_events(title_filter=None, date_filter=None):
    try:
        events = get_calendar()
        if not events:
            return []
        filtered_events = [
            event for event in events
            if (title_filter.lower() in event["title"].lower() if title_filter else True) and 
               (date_filter in event["start_at"] if date_filter else True)
        ]
        return filtered_events
    except Exception as e:
        logger.error(f"Erro ao buscar eventos do calendário: {str(e)}")
        return []

def get_username():
    user_data = make_request("/users/self")
    return user_data.get("name") if user_data else None

def list_courses(params=None):
    return make_request("/api/v1/courses", params)

def get_course_details(course_id, params=None):
    return make_request(f"/api/v1/courses/{course_id}", params)

def list_modules(course_id, params=None):
    return make_request(f"/api/v1/courses/{course_id}/modules", params)

def list_module_items(course_id, module_id, params=None):
    return make_request(f"/api/v1/courses/{course_id}/modules/{module_id}/items", params)

def get_courses():
    courses = list_courses(params={"per_page": 5})
    
    if isinstance(courses, dict):  # Se for um único curso, converta para lista
        courses = [courses]
    return courses if isinstance(courses, list) else []

def get_all_modules(courses):
    all_modules = []
    for course in courses:
        course_modules = list_modules(course_id=course["id"], params={"per_page": 5})
        if course_modules:
            for module in course_modules:
                module["course_name"] = course["name"]
                all_modules.append(module)
    return all_modules

def save_calendar_data():
    calendar_data = get_calendar_events()
    with open("./scraping/calendar_data.txt", "a") as file:
        for event in calendar_data:
            file.write(str(event))

def save_modules_data():
    courses = get_courses()
    modules_data = get_all_modules(courses)
    with open("./scraping/modules_data.txt", "a") as file:
        for module in modules_data:
            file.write(f"Módulos: {str(module)}")

def save_courses_data():
    courses_data = get_courses()
    with open("./scraping/courses_data.txt", "a") as file:
        file.write(f"Cursos: {str(courses_data)}")

if __name__ == "__main__":
    save_calendar_data()
    save_modules_data()
    save_courses_data()