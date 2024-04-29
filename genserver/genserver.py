import sys
import os
import json
import time
import asyncio
import redis
from fastapi import WebSocket
from celery_worker import _uuv_trajectory_producer
from models import TrajectoryGeneratorSpecification
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from settings import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_KV_STORE_PREFIX_GENERATOR,
    REDIS_SORTED_SET_PREFIX_GENERATOR,
    REDIS_SORTED_SET_GENERATORS,
)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

# Number of seconds to wait between UI updates
WAIT_TIME = 0.25

app = FastAPI()

# Serve static files and load jinja2 templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
# Make sure all data are flushed from redis on startup
r.flushall()


@app.get("/")
def home_page(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})


def format_timedelta(td, digits: int = 2) -> str:
    if digits < 0:
        ValueError("Input 'digits' < 0. Valid input is 'digits' >= 0.")
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    milliseconds = str(round(td.microseconds / 1_000_000, digits)).split(".")[-1]
    return f"{hours:02}:{minutes:02}:{seconds:>02}.{milliseconds:<0{digits}}"


def format_datetime(dt, digits: int = 2) -> str:
    if digits < 0:
        ValueError("Input 'digits' < 0. Valid input is 'digits' >= 0.")
    millisecond = str(round(dt.microsecond / 1_000_000, digits)).split(".")[-1]
    return f"{dt.hour:02}:{dt.minute:02}:{dt.second:>02}.{millisecond:<0{digits}}"


async def compile_generator_status_table(generator_ids: list[str]) -> str:
    rows = []
    for generator_id in generator_ids:
        # Extract the start time of the generator from the Redis KV-store
        metadata = json.loads(
            r.get(REDIS_KV_STORE_PREFIX_GENERATOR + "-" + generator_id)
        )

        # Determine start and running time for the generator
        start_time = datetime.fromisoformat(metadata["start_time"])
        current_time = datetime.now()
        running_time = current_time - start_time

        start_time = format_datetime(start_time)
        running_time = format_timedelta(running_time)

        rows.append(
            {
                "start_time": start_time,
                "running_time": running_time,
                "generator_id": generator_id,
            }
        )
    # Generate the full status table of all running generators
    table_template = templates.env.get_template("home/status_table/table.html")
    rendered_html = table_template.render(rows=rows)
    return rendered_html


@app.websocket("/ws/generators/status")
async def ws_generators_status(websocket: WebSocket) -> None:
    # Accept the incoming connection
    await websocket.accept()
    try:
        while True:
            generator_ids = [
                member.decode()
                for member in r.zrange(
                    REDIS_SORTED_SET_GENERATORS, 0, -1, withscores=False
                )
            ]

            table = await compile_generator_status_table(generator_ids=generator_ids)

            await websocket.send_text(table)

            # Wait a moment before continuing
            await asyncio.sleep(WAIT_TIME)
    except Exception as e:
        print(e)
    finally:
        try:
            # Try to close the websocket connection
            await websocket.close()
        except Exception as e:
            print(e)


@app.get("/generators/log/{generator_id}")
def home_page(request: Request, generator_id: str):
    return templates.TemplateResponse(
        "home/generators.html", {"request": request, "generator_id": generator_id}
    )


log_entry_template = """
    <div hx-swap-oob="beforeend:#content">
    <p>Index {index}: {message}</p>
    </div>
"""


async def compile_log_entries(log_entries: list[tuple[str, float]]) -> str:
    log = ""
    for log_entry in log_entries:
        msg, index = log_entry
        log += log_entry_template.format(index=int(index), message=msg.decode())
    return log


@app.websocket("/ws/generators/log/{generator_id}")
async def ws_generator_log(websocket: WebSocket, generator_id: str) -> None:
    # Accept the incoming connection
    await websocket.accept()
    try:
        log_entries = r.zrange(
            REDIS_SORTED_SET_PREFIX_GENERATOR + "-" + generator_id,
            0,
            -1,
            withscores=True,
        )
        # Track the number of entries we will display so far
        cardinality_seen = len(log_entries)

        # Compile the log entries into a single string and send it off
        log = await compile_log_entries(log_entries=log_entries)
        await websocket.send_text(log)

        # Wait a moment before continuing
        await asyncio.sleep(WAIT_TIME)

        while True:
            # Track the current number of log entries in the sorted set
            cardinality = r.zcard(
                REDIS_SORTED_SET_PREFIX_GENERATOR + "-" + generator_id
            )

            # Decide if we need to display any new log entries
            if cardinality == cardinality_seen:
                continue
            else:
                new_log_entries = r.zrange(
                    REDIS_SORTED_SET_PREFIX_GENERATOR + "-" + generator_id,
                    cardinality_seen,
                    cardinality_seen,
                    withscores=True,
                )
                # Update the current number of entries seen
                cardinality_seen = cardinality

                # Compile the log entries into a single string and send it off
                log = await compile_log_entries(log_entries=new_log_entries)
                await websocket.send_text(log)

            # Wait a moment before continuing
            await asyncio.sleep(WAIT_TIME)
    except Exception as e:
        print(e)
    finally:
        try:
            # Try to close the websocket connection
            await websocket.close()
        except Exception as e:
            print(e)


@app.post("/generators/{generator_id}/stop")
async def stop_task(generator_id: str):

    # Stop the specific generator with id 'generator_id' by removing it from
    # the sorted set consisting of all running generators
    r.zrem(REDIS_SORTED_SET_GENERATORS, generator_id)

    # Since the generator was removed from the sorted set, clean up all data
    # associated with the specific generator
    r.delete(REDIS_SORTED_SET_PREFIX_GENERATOR + "-" + generator_id)
    r.delete(REDIS_KV_STORE_PREFIX_GENERATOR + "-" + generator_id)

    return JSONResponse({"message": f"Generator '{generator_id}' shut down."}, 200)


@app.post("/producer/uuv/trajectory")
async def uuv_trajectory_producer(specification: TrajectoryGeneratorSpecification):
    scores = r.zmscore(
        key=REDIS_SORTED_SET_GENERATORS, members=[specification.identifier]
    )

    # If 'None' is not in the list then the identifier is not already in use
    if None in scores:
        # Insert the generator ID and corresponding current time into a sorted set
        r.zadd(REDIS_SORTED_SET_GENERATORS, {specification.identifier: time.time()})

        # Save some additional data about the generator: The start time
        metadata = json.dumps({"start_time": str(datetime.now().isoformat())})

        # Insert the additional data into the Redis Key-Value store
        r.set(
            REDIS_KV_STORE_PREFIX_GENERATOR + "-" + specification.identifier, metadata
        )

        # Start the generator
        _uuv_trajectory_producer.delay(specification.model_dump_json())

        return JSONResponse(
            {"message": f"Generator '{specification.identifier}' started."}, 200
        )
    else:
        # The identifier is already in use
        raise HTTPException(
            status_code=409,
            detail=f"The given identifier '{specification.identifier}' is already in use.",
        )
