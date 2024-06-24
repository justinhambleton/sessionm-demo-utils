import logging
import os
import subprocess
import asyncio
import signal
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import argparse

# Setup logging
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(filename=os.path.join(LOG_DIR, 'scheduler.log'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

async def run_script(script_path, enable_logging, context):
    start_time = datetime.now()
    logging.info(f"Job {script_path} with context '{context}' started at: {start_time}")
    print(f"Job {script_path} with context '{context}' started at: {start_time}")

    try:
        cmd = f"python3 {script_path} --context {context}"
        if enable_logging:
            cmd += " --enableLogging"

        result = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await result.communicate()

        end_time = datetime.now()
        logging.info(f"Job {script_path} with context '{context}' completed successfully at: {end_time}")
        logging.info(f"Job duration for {script_path}: {end_time - start_time}")
        logging.info(f"Job output for {script_path}: {stdout.decode()}")
        logging.info(f"Job error (if any) for {script_path}: {stderr.decode()}")

        print(f"Job {script_path} with context '{context}' completed successfully at: {end_time}")
        print(f"Job duration for {script_path}: {end_time - start_time}")
    except Exception as e:
        end_time = datetime.now()
        logging.error(f"Job {script_path} with context '{context}' failed at: {end_time}")
        logging.error(f"Job duration for {script_path}: {end_time - start_time}")
        logging.error(f"Job error for {script_path}: {str(e)}")

        print(f"Job {script_path} with context '{context}' failed at: {end_time}")
        print(f"Job duration for {script_path}: {end_time - start_time}")
        print(f"Job error for {script_path}: {str(e)}")

async def run_jobs(context, enable_logging):
    script_path = "generate-customers/generate_customers.py"
    await run_script(script_path, enable_logging, context)

def print_next_run_times(scheduler):
    jobs = scheduler.get_jobs()
    if jobs:
        for job in jobs:
            next_run_time = job.next_run_time
            if next_run_time:
                print(f"Next job {job.id} is scheduled to run at: {next_run_time}")
    else:
        print("No scheduled jobs.")

def shutdown(signum, frame):
    logging.info("Scheduler is shutting down...")
    print("Scheduler is shutting down...")
    scheduler.shutdown(wait=False)
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scheduler for running generate_customers.py script.')
    parser.add_argument('--context', choices=['retail', 'qsr', 'fuel'], required=True, help='Context for the data.')
    parser.add_argument('--enableLogging', action='store_true', help='Enable logging.')

    args = parser.parse_args()

    scheduler = AsyncIOScheduler()

    # Schedule the job to run immediately
    scheduler.add_job(run_jobs, args=[args.context, args.enableLogging], id='immediate_job')

    # Schedule the job to run once every hour after the initial run until 17:00 UTC
    now = datetime.utcnow()
    if now.time() < time(17, 0):
        scheduler.add_job(run_jobs, IntervalTrigger(hours=1, start_date=now, end_date=datetime.combine(now.date(), time(17, 0))), args=[args.context, args.enableLogging], id='hourly_job_today')

    # Schedule the job to run once every hour between 09:00 and 17:00 UTC, every day of the week
    scheduler.add_job(run_jobs, CronTrigger(minute='0', hour='9-17', timezone='UTC'), args=[args.context, args.enableLogging], id='hourly_job')

    scheduler.start()
    logging.info("Scheduler started")
    print("Scheduler started")

    print_next_run_times(scheduler)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Keep the script running
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        shutdown(None, None)
