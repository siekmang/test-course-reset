import requests

def get_course_candidates_by_name(course_name, subdomain, api_key):
    if not course_name:
        return []

    base_url = f"https://{subdomain}.instructure.com/api/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "CourseResetTool/1.0.0 (Greg Siekman; gsiekman@unity.edu)",
    }
    params = {
        "search_by": "course",
        "search_term": course_name,
        "per_page": 100,
    }

    try:
        response = requests.get(
            f"{base_url}/accounts/self/courses",
            headers=headers,
            params=params,
        )
        if not response.ok:
            raise RuntimeError(f"Canvas API error: {response.status_code}")

        courses = response.json()

        normalized = course_name.strip().lower()

        def matches(course):
            values = [
                str(v).strip().lower()
                for v in (course.get("name"), course.get("course_code"), course.get("sis_course_id"))
                if v
            ]
            return any(normalized in v for v in values)

        return [
            {
                "id": course.get("id"),
                "name": course.get("name"),
                "courseCode": course.get("course_code"),
                "sisCourseId": course.get("sis_course_id"),
            }
            for course in courses
            if matches(course)
        ]
    except Exception as e:
        print(f"Failed to fetch courses: {e}")
        return []
