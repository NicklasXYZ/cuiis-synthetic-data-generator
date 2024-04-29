from typing import Any
import datetime
import json
import time
import httpx
import redis
from celery import Celery
from uuv_trajectory_generator.trajectory_generator import (
    generate_path,
    sample_path,
    all_latlon_to_cartesian,
    cartesian_to_latlon,
)
from settings import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_URL,
    REDIS_SORTED_SET_PREFIX_GENERATOR,
    REDIS_SORTED_SET_GENERATORS,
)

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# Connect Celery to Redis
celery_app = Celery("celery-tasks", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.broker_connection_retry_on_startup = True


def compile_uuv_datapoint_request(
    noisy_sample_point: tuple, timestamp: str, identifier: str
) -> str:
    latitude, longitude = cartesian_to_latlon(
        noisy_sample_point[0], noisy_sample_point[1]
    )
    return json.dumps(
        {
            "latitude": latitude,
            "longitude": longitude,
            "elevation": noisy_sample_point[2],
            "timestamp": timestamp.isoformat(),
            "identifier": identifier,
        }
    )


@celery_app.task()
def _uuv_trajectory_producer(specification: str) -> None:
    # Load serialized 'TrajectoryGeneratorSpecification'
    specification = json.loads(specification)

    # Generate a detailed trace of a UUV path
    waypoints = all_latlon_to_cartesian(datapoints=specification["waypoints"])
    path = generate_path(
        coordinates=waypoints, turning_radius=specification["turning_radius"]
    )

    # Sample coordinates with corresponding timestamps along the path
    noisy_sample_points, timestamps, time_increments = sample_path(
        path=path,
        mean_time_delta=specification["mean_time_delta"],
        std_time_delta=specification["std_time_delta"],
        mean_speed=specification["mean_speed"],
        std_speed=specification["std_speed"],
        start_datetime=datetime.datetime.fromisoformat(specification["start_datetime"]),
        std_spatial=specification["std_spatial"],
    )

    # Create an 'index' for keeping track of the current coordinates and
    # timestamps to send off
    index = 0

    # Create an httpx client for sending POST requests with the coordinate
    # and timestamp data
    client = httpx.Client(timeout=2.5)
    while True:
        if index >= len(noisy_sample_points):
            # Since there are no more data to send, clean up the entry in the
            # sorted set containing all running generators
            r.zrem(REDIS_SORTED_SET_GENERATORS, specification["identifier"])
            break
        else:
            scores = r.zmscore(
                key=REDIS_SORTED_SET_GENERATORS, members=[specification["identifier"]]
            )
            # Check if the generator has been stopped manually by a 'POST' request
            # to '/generators/{generator_id}/stop'
            if None in scores:
                break
            else:
                json_data = compile_uuv_datapoint_request(
                    noisy_sample_point=noisy_sample_points[index],
                    timestamp=timestamps[index],
                    identifier=specification["identifier"],
                )
                client.request(
                    method="POST",
                    url=specification["url"],
                    data=json_data,
                )
                r.zadd(
                    REDIS_SORTED_SET_PREFIX_GENERATOR
                    + "-"
                    + specification["identifier"],
                    {json_data: index},
                )
                index += 1
                # print(f"Waiting: {time_increments[index]} seconds...")
                time.sleep(time_increments[index])
    client.close()
