import numpy as np


class Waypoint:
    """Waypoint data structure

    > *Attributes*

    * `FINAL_WAYPOINT_COLOR` (*type:* list of `float`, *value:* `[1.0, 0.5737, 0.0]`): RGB color for marker of the final waypoint in RViz
    * `OK_WAYPOINT` (*type:* list of `float`, *value:* `[0.1216, 0.4157, 0.8863]`): RGB color for marker of a successful waypoint in RViz
    * `FAILED_WAYPOINT` (*type:* list of `float`, *value:* `[1.0, 0.0, 0.0]`): RGB color for marker of a failed waypoint in RViz

    > *Input arguments*

    * `x` (*type:* `float`, *default:* `0`): X coordinate in meters
    * `y` (*type:* `float`, *default:* `0`): Y coordinate in meters
    * `z` (*type:* `float`, *default:* `0`): Z coordinate in meters
    * `max_forward_speed` (*type:* `float`, *default:* `0`): Reference maximum forward speed in m/s
    * `heading_offset` (*type:* `float`, *default:* `0`): Heading offset to be added to the computed heading reference in radians
    * `use_fixed_heading` (*type:* `float`, *default:* `False`): Use the heading offset as a fixed heading reference in radians
    * `inertial_frame_id` (*type:* `str`, *default:* `'world'`): Name of the inertial reference frame, options are `world` or `world_ned`
    * `radius_acceptance` (*type:* `float`, *default:* `0`): Radius around the waypoint where the vehicle can be considered to have reached the waypoint

    """

    def __init__(
        self,
        x=0,
        y=0,
        z=0,
        max_forward_speed=0,
        heading_offset=0,
        use_fixed_heading=False,
        inertial_frame_id="world",
        radius_acceptance=0.0,
    ):
        assert inertial_frame_id in ["world", "world_ned"], (
            "Invalid inertial reference frame, options"
            " are world or world_ned, provided={}".format(inertial_frame_id)
        )
        self._x = x
        self._y = y
        self._z = z
        # self._inertial_frame_id = inertial_frame_id
        self._max_forward_speed = max_forward_speed
        self._heading_offset = heading_offset
        # self._violates_constraint = False
        # self._use_fixed_heading = use_fixed_heading
        # self._radius_acceptance = radius_acceptance

    def __eq__(self, other):
        return self._x == other.x and self._y == other.y and self._z == other.z

    def __ne__(self, other):
        return self._x != other.x or self._y != other.y or self._z != other.z

    @property
    def x(self):
        """`float`: X coordinate of the waypoint in meters"""
        return self._x

    @property
    def y(self):
        """`float`: Y coordinate of the waypoint in meters"""
        return self._y

    @property
    def z(self):
        """`float`: Z coordinate of the waypoint in meters"""
        return self._z

    @property
    def pos(self):
        """`numpy.ndarray`: Position 3D vector"""
        return np.array([self._x, self._y, self._z])

    @pos.setter
    def pos(self, new_pos):
        if isinstance(new_pos, list):
            assert len(new_pos) == 3, "New position must have three elements"
        elif isinstance(new_pos, np.ndarray):
            assert new_pos.shape == (3,), "New position must have three elements"
        else:
            raise Exception("Invalid position vector size")
        self._x = new_pos[0]
        self._y = new_pos[1]
        self._z = new_pos[2]

    @property
    def violates_constraint(self):
        """`bool`: Flag on constraint violation for this waypoint"""
        return self._violates_constraint

    @violates_constraint.setter
    def violates_constraint(self, flag):
        self._violates_constraint = flag

    @property
    def max_forward_speed(self):
        """`float`: Maximum reference forward speed"""
        return self._max_forward_speed

    @max_forward_speed.setter
    def max_forward_speed(self, vel):
        self._max_forward_speed = vel

    @property
    def heading_offset(self):
        """`float`: Heading offset in radians"""
        return self._heading_offset

    @property
    def heading(self):
        """`float`: Heading reference stored for this waypoint in radians"""
        return self._heading

    @heading.setter
    def heading(self, angle):
        self._heading = angle

    @property
    def radius_of_acceptance(self):
        """`float`: Radius of acceptance in meters"""
        return self._radius_acceptance

    @radius_of_acceptance.setter
    def radius_of_acceptance(self, radius):
        assert radius >= 0, "Radius must be greater or equal to zero"
        self._radius_acceptance = radius

    @property
    def using_heading_offset(self):
        """`float`: Flag to use the heading offset"""
        return self._use_fixed_heading

    def dist(self, pos):
        """Compute distance of waypoint to a point

        > *Input arguments*

        * `pos` (*type:* list of `float`): 3D position vector

        > *Returns*

        Distance to point in meters
        """
        return np.sqrt(
            (self._x - pos[0]) ** 2 + (self._y - pos[1]) ** 2 + (self._z - pos[2]) ** 2
        )

    def calculate_heading(self, target):
        """Compute heading to target waypoint

        > *Input arguments*

        * `target` (*type:* `uuv_waypoints/Waypoint`): Target waypoint

        > *Returns*

        Heading angle in radians
        """
        dy = target.y - self.y
        dx = target.x - self.x
        return np.arctan2(dy, dx)
