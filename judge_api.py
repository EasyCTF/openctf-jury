import logging
import time
from functools import wraps
from typing import Any, Dict, Optional

import requests

import config
from languages import languages
from models import ExecutionResult, Problem, Job, JobVerdict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.info('Starting up')


problems = {}

default_headers = {
    'api_key': config.JUDGE_API_KEY,
}


def retry_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        retry_freq = kwargs.pop('retry_freq', 1)
        while True:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                if retry_freq:
                    logger.warning('Failed to connect to judge API, retrying in %d seconds.', retry_freq)
                    time.sleep(retry_freq)
                else:
                    logger.warning('Failed to connect to judge API, not retrying.')
                    return None

    return wrapper


@retry_connection
def get(url: str, headers: Dict[str, str]=None):
    headers_to_send = {}
    headers_to_send.update(default_headers)
    if headers:
        headers_to_send.update(headers)
    return requests.get(url, headers=headers_to_send)


@retry_connection
def post(url: str, data: Dict[str, Any]=None, headers: Dict[str, str]=None):
    headers_to_send = {}
    headers_to_send.update(default_headers)
    if headers:
        headers_to_send.update(headers)
    return requests.post(url, data=data, headers=headers_to_send)


def jobs_claim():
    response = post(config.JUDGE_API_URLS['jobs_claim'])
    if not response or response.status_code == 204:
        return None
    job_dict = response.json()

    if job_dict['problem_id']:
        if not problems_get(job_dict['problem_id']):
            return None

    job_dict['problem'] = problems[job_dict.pop('problem_id')]

    if job_dict['language'] not in languages:
        logger.error('Language %s not supported!' % job_dict['language'])
        return None
    job_dict['language'] = languages[job_dict['language']]

    return Job(**job_dict)


def jobs_submit(result: ExecutionResult):
    response = post(config.JUDGE_API_URLS['jobs_submit'] % result.job.id, data={
        'verification_code': result.job.verification_code,
        'verdict': result.verdict.value if result.verdict else '',
        'last_ran_case': result.last_ran_case,
        'execution_time': result.execution_time,
        'execution_memory': result.execution_memory,
    })
    return response and response.status_code == 200


def jobs_release(job: Job, retry_freq=1):
    response = post(config.JUDGE_API_URLS['jobs_cancel'] % job.id, data={
        'verification_code': job.verification_code,
    }, retry_freq=retry_freq)
    return response and response.status_code == 200


def problems_refresh():
    logger.info('Refreshing problems...')

    global problems
    response = get(config.JUDGE_API_URLS['problems_list'])
    if response and response.status_code == 200:
        for problem_dict in response.json():
            problem_dict['generator_language'] = languages[problem_dict['generator_language']]
            problem_dict['grader_language'] = languages[problem_dict['grader_language']]
            if 'source_verifier_language' in problem_dict and problem_dict['source_verifier_language']:
                problem_dict['source_verifier_language'] = languages[problem_dict['source_verifier_language']]
            problems[problem_dict['id']] = Problem(**problem_dict)
        return True
    else:
        return False


def problems_get(problem_id: int):
    headers = {}
    if problem_id in problems:
        headers['If-Modified-Since'] = str(int(problems[problem_id].last_modified))
    response = get(config.JUDGE_API_URLS['problems_get'] % problem_id, headers=headers)
    if response:
        if response.status_code == 200:
            problem_dict = response.json()
            problem_dict['generator_language'] = languages[problem_dict['generator_language']]
            problem_dict['grader_language'] = languages[problem_dict['grader_language']]
            if 'source_verifier_language' in problem_dict and problem_dict['source_verifier_language']:
                problem_dict['source_verifier_language'] = languages[problem_dict['source_verifier_language']]
            problems[problem_id] = Problem(**problem_dict)
            logger.info('Got problem %d.' % problem_id)
            return True
        elif response.status_code == 304:
            return True
    return False
