import sys
import os
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from uuv_trajectory_generator.trajectory_generator import (
    generate_path,
    sample_path,
    all_latlon_to_cartesian,
    cartesian_to_latlon,
)


# Testing...
if __name__ == "__main__":
    waypoints = [
        {"latitude": 43.187634, "longitude": 27.926699, "elevation": 0.0},
        {"latitude": 43.190732, "longitude": 27.926570, "elevation": 3.0},
        {"latitude": 43.194048, "longitude": 27.926184, "elevation": 6.0},
        {"latitude": 43.195237, "longitude": 27.929190, "elevation": 9.0},
        {"latitude": 43.194361, "longitude": 27.930994, "elevation": 12.0},
        {"latitude": 43.192546, "longitude": 27.931337, "elevation": 15.0},
        {"latitude": 43.189793, "longitude": 27.931809, "elevation": 12.0},
        {"latitude": 43.188166, "longitude": 27.931808, "elevation": 9.0},
        {"latitude": 43.189042, "longitude": 27.929103, "elevation": 6.0},
        {"latitude": 43.192265, "longitude": 27.928330, "elevation": 4.0},
    ]
    # Sampling parameters
    mean_time_delta = 10.0
    std_time_delta = 1.5
    mean_speed = 1.25
    std_speed = 0.25
    start_datetime = datetime.now()
    std_spatial = 0.25
    turning_radius = 25

    coordinates = all_latlon_to_cartesian(datapoints=waypoints)

    path = generate_path(coordinates=coordinates, turning_radius=turning_radius)
    noisy_sample_points, timestamps, time_increments = sample_path(
        path=path,
        mean_time_delta=mean_time_delta,
        std_time_delta=std_time_delta,
        mean_speed=mean_speed,
        std_speed=std_speed,
        start_datetime=start_datetime,
        std_spatial=std_spatial,
    )

    noisy_sample_points = [
        (*cartesian_to_latlon(x, y), z) for (x, y, z) in noisy_sample_points
    ]

    method = "3d"

    if method == "2d":
        plt.scatter(
            [dp[0] for dp in noisy_sample_points], [dp[1] for dp in noisy_sample_points]
        )
        plt.show()
    elif method == "3d":
        fig = plt.figure(figsize=(15, 15))
        ax = fig.add_subplot(111, projection="3d")
        # Sample path
        ax.plot(
            [dp[0] for dp in noisy_sample_points],
            [dp[1] for dp in noisy_sample_points],
            [dp[2] for dp in noisy_sample_points],
        )
        # Waypoints
        ax.plot(
            [dp["latitude"] for dp in waypoints],
            [dp["longitude"] for dp in waypoints],
            [dp["elevation"] for dp in waypoints],
            "ro",
        )
        plt.show()
