import logging
import signal
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.info('Starting up')

import executor
from models import Job
import judge_api

current_job = None  # type: Job


def shutdown(signal, frame):
    logger.warning('Shutting down...')
    if current_job:
        judge_api.jobs_release(current_job, retry_freq=0)
    exit(0)


def loop():
    global current_job
    job = judge_api.jobs_claim()
    current_job = job
    if not job:
        logger.debug('No jobs available.')
        return False
    logger.info('Got job %d.', job.id)

    for execution_result in executor.run_job(job):
        # execution_result is partial here

        logger.info('Job %d partially judged; case: %d, time: %.2f, memory: %d',
                    job.id, execution_result.last_ran_case, execution_result.execution_time,
                    execution_result.execution_memory)

        if execution_result.verdict:
            # This should be the last value returned by run_job
            logger.info('Job %d finished with verdict %s.' % (job.id, execution_result.verdict.value))

        if judge_api.jobs_submit(execution_result):
            logger.info('Job %d successfully partially submitted.' % job.id)
        else:
            logger.info('Job %d failed to partially submit.' % job.id)

    return True


if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    judge_api.problems_refresh()

    while True:
        if not loop():
            time.sleep(1)
