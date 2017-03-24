import os
import pathlib
from typing import Dict


def load_dotenv():
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())


load_dotenv()

APP_ROOT = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
CONFINE_PATH = APP_ROOT / 'confine'

JUDGE_URL = os.getenv('JUDGE_URL', 'http://localhost:5000')  # type: str

JUDGE_API_URLS = {
    'jobs_claim': '/jobs/claim',
    'jobs_submit': '/jobs/%d/submit',
    'problems_list': '/problems',
    'problems_get': '/problems/%d',
}  # type: Dict[str, str]

JUDGE_API_KEY = os.getenv('JUDGE_API_KEY', '')

for k, v in JUDGE_API_URLS.items():
    JUDGE_API_URLS[k] = JUDGE_URL + v

COMPILATION_TIME_LIMIT = 10
GRADER_TIME_LIMIT = 10

PARTIAL_JOB_SUBMIT_TIME_THRESHOLD = 2 # Seconds
PARTIAL_JOB_SUBMIT_CASES_THRESHOLD = 10
