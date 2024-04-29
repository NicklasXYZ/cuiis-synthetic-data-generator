from pydantic import BaseModel, field_validator, HttpUrl, Field
import datetime
from typing import Optional


class Waypoint(BaseModel):
    latitude: float
    longitude: float
    elevation: float


class TrajectoryGeneratorSpecification(BaseModel):
    identifier: str = Field(
        ...,
        description="A unique identifier for the trajectory generator that should not contain spaces.",
    )
    url: HttpUrl = Field(
        ...,
        description="The URL to which the generated data will be sent as POST requests.",
    )
    waypoints: list[Waypoint] = Field(
        ...,
        description="A list of geographical waypoints the UUV will navigate through; requires at least two waypoints.",
    )
    start_datetime: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.now,
        description="The initial timestamp for the generated trajectory data stream.",
    )
    # The average time (s) between datapoints
    mean_time_delta: Optional[float] = Field(
        default=7.5,
        description="Average time interval in seconds between consecutive datapoints in the trajectory.",
    )
    # The standard deviation (s) associated with 'mean_time_delta'
    # -> Adds a variation in the time between generated timestamps
    std_time_delta: Optional[float] = Field(
        default=1.5,
        description="Standard deviation in time intervals, introducing variability in the frequency of datapoints.",
    )
    # The average speed (m/s) of the UUV
    mean_speed: Optional[float] = Field(
        default=1.25, description="Average speed of the UUV in meters per second."
    )
    # The standard deviation (s) associated with 'mean_speed'
    # -> Adds a variation in the mean speed of the UUV
    std_speed: Optional[float] = Field(
        default=0.25,
        description="Standard deviation of the UUV's speed, adding variability to the mean speed.",
    )
    # The standard deviation (m) associated with a geospatial datapoint
    # -> Adds noise to the geospatial datapoint
    std_spatial: Optional[float] = Field(
        default=0.25,
        description="Standard deviation applied to each geospatial datapoint, introducing spatial noise to the trajectory.",
    )
    # The turning radius (m) of the UUV
    turning_radius: Optional[float] = Field(
        default=25,
        description="Turning radius of the UUV in meters, affecting the navigational capabilities around waypoints.",
    )

    @field_validator("identifier")
    def validate_identifier(cls, value) -> str:
        # Check if the identifier contains any whitespaces
        if any(char.isspace() for char in value):
            raise ValueError("The 'identifier' cannot contain whitespaces.")
        return value

    @field_validator("waypoints")
    def validate_waypoints(cls, value) -> list[Waypoint]:
        # Check if the identifier contains any whitespaces
        if len(value) < 2:
            raise ValueError(
                "The list 'waypoints' need to contain at least 2 waypoints."
            )
        return value

    @field_validator(
        "mean_time_delta",
        "std_time_delta",
        "std_speed",
        "std_spatial",
        "turning_radius",
    )
    def check_positive(cls, value, field) -> float:
        # Ensure that the provided values are positive
        if value < 0:
            raise ValueError(f"The field '{field.field_name}' must be positive.")
        return value
