import os
import requests
from dotenv import load_dotenv

load_dotenv()

def course_reset():
    subdomain = os.getenv('SUBDOMAIN')
    target_course_id = os.getenv('TARGET_COURSE_ID')
    source_course_id = os.getenv('SOURCE_COURSE_ID')
    api_key = os.getenv('API_KEY')

    if subdomain is None:
        # Prompt for subdomain
        return NotImplementedError
    elif target_course_id is None:
        # Prompt for ID from course to reset
        return NotImplementedError
    elif source_course_id is None:
        # Prompt for ID from course to pull from
        return NotImplementedError
    elif api_key is None:
        # Prompt for API Key
        return NotImplementedError

    base_url = f"https://{subdomain}.instructure.com/api/v1"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "CourseResetTool/1.0.0 (Greg Siekman; gsiekman@unity.edu)",
    }

    reset_response = requests.post(
        f"{base_url}/courses/{target_course_id}/reset_content",
        headers=headers
    )

    if(not reset_response.ok):
        raise RuntimeError(f"Reset failed: {reset_response.status_code} - {reset_response.text}")

    reset_data = reset_response.json()
    new_course_id = reset_data.get('id', target_course_id)

    payload = {
        "migration_type": "course_copy_importer",
        "settings": {
            "source_course_id": source_course_id,
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

    return {
        "targetCourseId": new_course_id,
        "sourceCourseId": source_course_id,
    }
