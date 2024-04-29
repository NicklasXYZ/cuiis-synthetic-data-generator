from datetime import datetime
import time
import httpx

# Specify some test data (data generator specification) to send
# along to the UUV trajectory data generator   
test_data1 = {
    "identifier": "uuv1",
    "url": "http://conserver:8081/consumer/uuv/trajectory",
    "waypoints": [
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
    ],
    "start_datetime": datetime.now().isoformat(),
    "mean_time_delta": 1.0,
    "std_time_delta": 0.10,
    "mean_speed": 1.0,
    "std_speed": 0.25,
    "std_spatial": 0.25,
    "turning_radius": 5,
}

if __name__ == "__main__":

    # Specify the number of requests to send
    # to test generator concurrency
    n_requests = 1
    for i in range(n_requests):
        test_data1["identifier"] = f"uuv{i}"
        httpx.request(
            method="POST",
            url="http://0.0.0.0:8080/producer/uuv/trajectory",
            data=test_data1,
        )
        time.sleep(1.0)
