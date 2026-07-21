import requests

def get_course_candidates_by_name(course_name, subdomain, api_key):
    base_url = f"https://{subdomain}.instructure.com/api/v1"
    headers = {"Authorization": f"Bearer {api_key}"}

    # requests automatically handles URL encoding for params
    params = {
        "search_term": course_name,
        "per_page": 100
    }

    try:
        response = requests.get(
            f"{base_url}/courses",
            headers=headers,
            params=params
        )

        if not response.ok:
            raise RuntimeError(f"Canvas API error: {response.status_code}")

        courses = response.json()
        return [
            {
                "id": course.get("id"),
                "name": course.get("name"),
                "courseCode": course.get("course_code")
            }
            for course in courses
        ]

    except Exception as e:
        print(f"Failed to fetch courses: {e}")
        return []
