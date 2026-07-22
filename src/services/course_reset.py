import os
import requests
from dotenv import load_dotenv

load_dotenv()

def course_reset(target_course_id: str | None = None, source_course_id: str | None = None):
    subdomain = os.getenv('SUBDOMAIN')
    api_key = os.getenv('API_KEY')
    target_course = target_course_id or os.getenv('TARGET_COURSE_ID')
    source_course = source_course_id or os.getenv('SOURCE_COURSE_ID')

    if not all([subdomain, api_key, target_course, source_course]):
            raise ValueError("Missing required credentials or course info configuration. Run configuration.")

    base_url = f"https://{subdomain}.instructure.com/api/v1"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "CourseResetTool/1.0.0 (Greg Siekman; gsiekman@unity.edu)",
    }

    reset_response = requests.post(
        f"{base_url}/courses/{target_course}/reset_content",
        headers=headers
    )

    if(not reset_response.ok):
        raise RuntimeError(f"Reset failed: {reset_response.status_code} - {reset_response.text}")

    reset_data = reset_response.json()
    new_course_id = reset_data.get('id', target_course)

    payload = {
        "migration_type": "course_copy_importer",
        "settings": {
            "source_course_id": source_course,
        }
    }

    import_response = requests.post(
        f"{base_url}/courses/{new_course_id}/content_migrations",
        headers=headers,
        json=payload
    )

    print("Import result status: ", import_response.status_code)

    if not import_response.ok:
        raise RuntimeError(f"Import failed: {import_response.status_code} - {import_response.text}")

    return new_course_id
