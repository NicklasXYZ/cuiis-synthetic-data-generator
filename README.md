# CUIIS Synthetic Data Generator

The CUIIS Synthetic Data Generator is designed to produce realistic synthetic data:

- Geospatial trajectory data for Underwater Unmanned Vehicles (UUVs)
- Physiological data for divers

## Prerequisites

Ensure Docker and Docker Compose are installed. For installation instructions, refer to the [Docker documentation](https://docs.docker.com/get-docker/)

### Installation

To deploy the application, follow these steps:

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Build Docker images, by navigating to the project directory and run:

```bash
sudo docker-compose build
```

3. Start the application:

```bash
sudo docker-compose up
```

4. Access the application, by opening a web browser and navigating to:

```plaintext
http://localhost:8080/
```

## Usage


1. Select the data generator type: Open the dropdown menu and choose 'UUV Trajectory Data' as shown below.

![img](/imgs/select.png)

2. Configure the data generator:
Upon selection, a textarea will appear containing example JSON data, necessary for configuring the data generator. Reference the API documentation (running at [http://0.0.0.0:8080/](http://0.0.0.0:8080/)) for detailed parameter descriptions.

![img](/imgs/docs.png)

Fill out the textarea with the required JSON parameters and click the blue button at the bottom of the page. This action sends a POST request to the backend, initiating the data generation process.

4. Manage multiple generators:
Each data generator can be uniquely identified and managed separately, as shown below.

![img](/imgs/identifier.png)

5. View generated data: Click on a generator's unique identifier to view and inspect its output data:

![img](/imgs/log.png)

