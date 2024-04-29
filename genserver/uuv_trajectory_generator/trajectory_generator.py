from typing import Any
from pyproj import Proj
import numpy as np
import shapely
from uuv_waypoints.waypoint import Waypoint
from uuv_waypoints.waypoint_set import WaypointSet
from uuv_trajectory_generator.path_generator import DubinsInterpolator
from datetime import datetime, timedelta

from settings import (
    UTM_ZONE,
)


def latlon_to_cartesian(lat: float, lon: float) -> tuple[float, float]:
    # Define the UTM projection for the region
    utm_proj = Proj(proj="utm", zone=UTM_ZONE, ellps="WGS84")
    # Convert latitude and longitude to northing and easting coordinates in meters
    easting, northing = utm_proj(lon, lat)
    return northing, easting


def all_latlon_to_cartesian(
    datapoints: list[dict[str, Any]]
) -> tuple[float, float, float]:
    # Convert the latitude/longitude points to cartesian (in a local UTM coordinate system)
    coordinates = [
        (
            *latlon_to_cartesian(dict["latitude"], dict["longitude"]),
            dict["elevation"],
        )
        for dict in datapoints
    ]
    return coordinates


def cartesian_to_latlon(northing: float, easting: float) -> tuple[float, float]:
    # Define the UTM projection based on the zone and hemisphere
    utm_proj = Proj(proj="utm", zone=UTM_ZONE, ellps="WGS84")
    # Convert easting and northing back to latitude and longitude
    lon, lat = utm_proj(easting, northing, inverse=True)
    return lat, lon


def all_cartesian_to_latlon(
    datapoints: list[dict[str, Any]]
) -> tuple[float, float, float]:
    # Convert the points in a local UTM coordinate system to latitude/longitude points
    coordinates = [
        (
            *cartesian_to_latlon(dict["northing"], dict["easting"]),
            dict["elevation"],
        )
        for dict in datapoints
    ]
    return coordinates


def generate_path(
    coordinates: dict[str, Any], turning_radius: float
) -> shapely.LineString:
    # NOTE: It is important here that the coordinates are cartesian coordinates!!!
    waypoints = WaypointSet()
    for i in range(len(coordinates)):
        waypoints.add_waypoint(
            Waypoint(
                coordinates[i][0],
                coordinates[i][1],
                coordinates[i][2],
                max_forward_speed=0.5,
            )
        )

    # Generate a (detailed) path through a set of given waypoints
    interpolator = DubinsInterpolator(radius=turning_radius)
    interpolator.init_waypoints(waypoints)
    valid_input = interpolator.init_interpolator()

    if valid_input:
        path = [
            (point.x, point.y, point.z)
            for point in interpolator.get_samples(max_time=None)
        ]

        return shapely.LineString(path)
    else:
        raise ValueError(
            "The 'waypoints' list is not valid. At least 2 waypoints needs to be provided."
        )


def add_spatial_noise(sample_points: list, std_spatial: float) -> list:
    rand_arr = np.random.normal(0, std_spatial, size=(len(sample_points), 3))
    for i in range(rand_arr.shape[0]):
        rand_arr[i, 0] += sample_points[i].x
        rand_arr[i, 1] += sample_points[i].y
        rand_arr[i, 2] += sample_points[i].z
    return list(shapely.LineString(rand_arr.tolist()).coords)


def sample_path(
    path: shapely.LineString,
    mean_time_delta: float,
    std_time_delta: float,
    mean_speed: float,
    std_speed: float,
    start_datetime: datetime,
    std_spatial: float,
) -> tuple[list, list, list]:
    # Working defaults:
    # mean_time_delta = 10.0
    # std_time_delta = 1.5
    # mean_speed = 1.25
    # std_speed = 0.25
    # start_datetime = datetime.now()
    # std_spatial = 0.25

    # Sampe points along the linestring representing a detailed UUV path
    dxs = [0.0]
    dts = [0.0]
    counter = 0
    path_length = path.length
    if path_length > 0:
        while True:
            # Sample a location along the path by:
            # - Determining a random time increment 'dt'
            # - Moving along the path based on:
            #   -> A sampled speed (m/s)
            #   -> A time increment (s)
            dt = mean_time_delta + np.abs(np.random.normal(0.0, std_time_delta))
            dx = (mean_speed + np.random.normal(0.0, std_speed)) * dt
            dx_next = dxs[counter] + dx
            if dx_next > path_length:
                break
            else:
                dts.append(dt)
                dxs.append(dx_next)
                counter += 1
        _dts = np.cumsum(dts)
        _dxs = [v / path_length for v in dxs]

        # Generate the timestamps based on:
        # - Random temporal increments '_dts'
        timestamps = [
            start_datetime + timedelta(seconds=_dts[i]) for i in range(len(_dts))
        ]

        # Generate the corresponding spatial sample points based on:
        # - Random spatial increments '_dxs' along the linestring 'path'
        sample_points = [
            path.interpolate(_dxs[i], normalized=True) for i in range(len(_dxs))
        ]
        # Add noise to the sample points
        noisy_sample_points = add_spatial_noise(
            sample_points=sample_points, std_spatial=std_spatial
        )

        return noisy_sample_points, timestamps, dts
    else:
        raise ValueError(
            "The 'Linestring' length is zero. Start and end location must thus be the same."
        )
