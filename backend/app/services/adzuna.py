
import os
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


def fetch_adzuna_jobs(
    query="software engineer",
    location="India",
    page=1,
    results_per_page=20
):
    """
    Fetch real-time job listings from Adzuna.
    """

    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        raise ValueError("Adzuna API credentials are missing.")

    url = (
        f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"
    )

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "what": query,
        "where": location,
        "content-type": "application/json"
    }

    request_url = f"{url}?{urlencode(params)}"

    request = Request(
        request_url,
        headers={"Accept": "application/json"}
    )

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        return data.get("results", [])

    except HTTPError as e:
        raise RuntimeError(
            f"Adzuna API HTTP error: {e.code}"
        ) from e

    except URLError as e:
        raise RuntimeError(
            f"Could not connect to Adzuna: {e.reason}"
        ) from e

    except TimeoutError as e:
        raise RuntimeError(
            "Adzuna API request timed out."
        ) from e

    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Adzuna returned an invalid JSON response."
        ) from e
