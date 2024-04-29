import numpy as np
import os
import yaml
from uuv_waypoints.waypoint import Waypoint


class WaypointSet:
    """Set of waypoints.

    > *Input arguments*

    * `scale` (*type:* `float`, *default:* `0.1`): Scale of the spherical marker for waypoints
    * `inertial_frame_id` (*type:* `str`, *default:* `'world'`): Name of the inertial reference frame, options are `world` and `world_ned` for `ENU` and `NED` inertial reference frames, respectively
    * `max_surge_speed` (*type:* `float`, *default:* `None`): Max. surge speed in m/s associated with each waypoint
    """

    def __init__(self, scale=0.1, inertial_frame_id="world", max_surge_speed=None):
        assert inertial_frame_id in ["world", "world_ned"]
        self._waypoints = list()
        self._violates_constraint = False
        self._scale = scale
        self._inertial_frame_id = inertial_frame_id
        self._max_surge_speed = max_surge_speed

    def __str__(self):
        if self.num_waypoints:
            msg = "================================\n"
            msg += "List of waypoints\n"
            msg += "================================\n"
            for i in range(self.num_waypoints):
                msg += self.get_waypoint(i).__str__()
                msg += "---\n"
            msg += "Number of waypoints = %d\n" % self.num_waypoints
            msg += "Number of valid waypoints = %d\n" % self.num_waypoints
            msg += "Inertial frame ID = %s\n" % self._inertial_frame_id
            return msg
        else:
            return "Waypoint set is empty"

    @property
    def num_waypoints(self):
        """`int`: Number of waypoints"""
        return len(self._waypoints)

    @property
    def x(self):
        """`list`: List of the X-coordinates of all waypoints"""
        return [wp.x for wp in self._waypoints]

    @property
    def y(self):
        """`list`: List of the Y-coordinates of all waypoints"""
        return [wp.y for wp in self._waypoints]

    @property
    def z(self):
        """`list`: List of the Z-coordinates of all waypoints"""
        return [wp.z for wp in self._waypoints]

    @property
    def is_empty(self):
        """`bool`: True if the list of waypoints is empty"""
        return len(self._waypoints) == 0

    @property
    def inertial_frame_id(self):
        """`str`: Name of inertial reference frame"""
        return self._inertial_frame_id

    @inertial_frame_id.setter
    def inertial_frame_id(self, frame_id):
        assert frame_id in [
            "world",
            "world_ned",
        ], "Inertial reference frame can only be either world or world_ned"
        self._inertial_frame_id = frame_id

    def clear_waypoints(self):
        """Clear the list of waypoints"""
        self._waypoints = list()

    def set_constraint_status(self, index, flag):
        """Set the flag violates_constraint to a waypoint

        > *Input arguments*

        * `index` (*type:* `int`): Index of the waypoints
        * `flag` (*type:* `bool`): True, if waypoint violates a constraint

        > *Returns*

        `True` if successful, and `False` if the waypoint `index` is outsite of the list's range.
        """
        if index < 0 or index >= len(self._waypoints):
            return False
        self._waypoints[index].violates_constraint = flag
        return True

    def get_waypoint(self, index):
        """Return a waypoint

        > *Input arguments*

        * `index` (*type:* `int`): Index of the waypoint

        > *Returns*

        Return a waypoint as `uuv_waypoints.Waypoint` or `None` if `index` is outside of range.
        """
        if index < 0 or index >= len(self._waypoints):
            return None
        return self._waypoints[index]

    def add_waypoint(self, waypoint, add_to_beginning=False):
        """Add a waypoint to the set

        > *Input arguments*

        * `waypoint` (*type:* `uuv_waypoints.Waypoint`): Waypoint object
        * `add_to_beginning` (*type:* `bool`, *default:* `False`): If `True`, add the waypoint to the beginning of the list.

        > *Returns*

        `True` if waypoint was added to the set. `False` if a repeated waypoint is already found in the set.
        """
        if len(self._waypoints):
            if self._waypoints[-1] != waypoint:
                if not add_to_beginning:
                    self._waypoints.append(waypoint)
                else:
                    self._waypoints = [waypoint] + self._waypoints
            else:
                print("Cannot add repeated waypoint")
                return False
        else:
            if not add_to_beginning:
                self._waypoints.append(waypoint)
            else:
                self._waypoints = [waypoint] + self._waypoints
        return True

    def get_start_waypoint(self):
        """Return the starting waypoint

        > *Returns*

        A `uuv_waypoints.Waypoint` object or None, if the list of waypoints is empty.
        """
        if len(self._waypoints):
            return self._waypoints[0]
        else:
            return None

    def get_last_waypoint(self):
        """Return the final waypoint

        > *Returns*

        A `uuv_waypoints.Waypoint` object or None, if the list of waypoints is empty.
        """
        if len(self._waypoints):
            return self._waypoints[-1]
        return None

    def remove_waypoint(self, waypoint):
        """Remove waypoint from set.

        > *Input arguments*

        * `waypoint` (*type:* `uuv_waypoints.Waypoint`): Waypoint object
        """
        new_waypoints = list()
        for point in self._waypoints:
            if point == waypoint:
                continue
            new_waypoints.append(point)
        self._waypoints = new_waypoints

    def read_from_file(self, filename):
        """Read waypoint set from a YAML file.

        > *Input arguments*

        * `filename` (*type:* `str`): Filename of the waypoint set

        > *Returns*

        `True` if waypoint set file could be parsed, `False`, otherwise.
        """
        if not os.path.isfile(filename):
            print("Invalid waypoint filename, filename={}".format(filename))
            return False
        try:
            self.clear_waypoints()
            with open(filename, "r") as wp_file:
                wps = yaml.load(wp_file)
                if isinstance(wps, list):
                    for wp_data in wps:
                        wp = Waypoint(
                            x=wp_data["point"][0],
                            y=wp_data["point"][1],
                            z=wp_data["point"][2],
                            max_forward_speed=wp_data["max_forward_speed"],
                            heading_offset=wp_data["heading"],
                            use_fixed_heading=wp_data["use_fixed_heading"],
                            inertial_frame_id="world",
                        )
                        self.add_waypoint(wp)
                    self._inertial_frame_id = "world"
                else:
                    assert (
                        "inertial_frame_id" in wps
                    ), "Waypoint input has no inertial_frame_id key"
                    assert "waypoints" in wps
                    assert wps["inertial_frame_id"] in ["world", "world_ned"]
                    self._inertial_frame_id = wps["inertial_frame_id"]
                    for wp_data in wps["waypoints"]:
                        wp = Waypoint(
                            x=wp_data["point"][0],
                            y=wp_data["point"][1],
                            z=wp_data["point"][2],
                            max_forward_speed=wp_data["max_forward_speed"],
                            heading_offset=wp_data["heading"],
                            use_fixed_heading=wp_data["use_fixed_heading"],
                            inertial_frame_id=wps["inertial_frame_id"],
                        )
                        self.add_waypoint(wp)
        except Exception as e:
            print("Error while loading the file, message={}".format(e))
            return False
        return True

    def export_to_file(self, path, filename):
        """Export waypoint set to YAML file.

        > *Input arguments*

        * `path` (*type:* `str`): Path to the folder containing the file
        * `filename` (*type:* `str`): Name of the YAML file.

        > *Returns*

        `True` is waypoints could be exported to file. `False`, otherwise.
        """
        try:
            output = dict(inertial_frame_id=self._inertial_frame_id, waypoints=list())
            for wp in self._waypoints:
                wp_elem = dict(
                    point=[float(wp.x), float(wp.y), float(wp.z)],
                    max_forward_speed=float(wp._max_forward_speed),
                    heading=float(
                        wp._heading_offset if wp._heading_offset is not None else 0.0
                    ),
                    use_fixed_heading=bool(wp._use_fixed_heading),
                )
                output["waypoints"].append(wp_elem)
            with open(os.path.join(path, filename), "w") as wp_file:
                yaml.dump(output, wp_file, default_flow_style=False)
            return True
        except Exception as e:
            print("Error occured while exporting waypoint file, message={}".format(e))
            return False

    def dist_to_waypoint(self, pos, index=0):
        """Compute the distance of a waypoint in the set to point

        > *Input arguments*

        * `pos` (*type:* list of `float`): 3D point as a list of coordinates
        * `index` (*type:* `int`, *default:* `0`): Waypoint index in set

        > *Returns*

        Distance between `pos` and the waypoint in `index`. `None` if waypoint set is empty.
        """
        wp = self.get_waypoint(index)
        if wp is not None:
            return wp.dist(pos)
        return None

    def set_radius_of_acceptance(self, index, radius):
        """Set the radius of acceptance around each waypoint
        inside which a vehicle is considered to have reached
        a waypoint.

        > *Input arguments*

        * `index` (*type:* `int`): Index of the waypoint
        * `radius` (*type:* `float`): Radius of the sphere representing the volume of acceptance
        """
        if index >= 0 and index < len(self._waypoints):
            self._waypoints[index].radius_of_acceptance = radius

    def get_radius_of_acceptance(self, index):
        """Return the radius of acceptance for a waypoint

        > *Input arguments*

        * `index` (*type:* `int`): Index of the waypoint

        > *Returns*

        Radius of acceptance for the waypoint in position
        given by `index` as a `float`. `None` if waypoint
        set is empty.
        """
        if index >= 0 and index < len(self._waypoints):
            return self._waypoints[index].radius_of_acceptance
        else:
            return None

    def generate_circle(
        self,
        radius,
        center,
        num_points,
        max_forward_speed,
        theta_offset=0.0,
        heading_offset=0.0,
        append=False,
    ):
        """Generate a set of waypoints describing a circle

        > *Input arguments*

        * `radius` (*type:* `float`): Radius of the circle in meters
        * `num_points` (*type:* `int`): Number of waypoints to be generated
        * `max_forward_speed` (*type:* `float`): Max. forward speed set to each waypoint in m/s
        * `theta_offset` (*type:* `float`, *default:* `0`): Angle offset to start generating the waypoints in radians
        * `heading_offset` (*type:* `float`, *default:* `0`): Heading offset set to the reference heading of the vehicle in radians
        * `append` (*type:* `bool`, *default:* `False`): If `True`, append the generated waypoints to the existent waypoints in the set

        > *Returns*

        `True` if the circle was successfully generated, `False`, otherwise
        """
        if radius <= 0:
            print("Invalid radius, value={}".format(radius))
            return False

        if num_points <= 0:
            print("Invalid number of samples, value={}".format(num_points))
            return False

        if max_forward_speed <= 0:
            print(
                "Invalid absolute maximum velocity, value={}".format(max_forward_speed)
            )
            return False

        if not append:
            # Clear current list
            self.clear_waypoints()

        step_theta = 2 * np.pi / num_points
        for i in range(num_points):
            angle = i * step_theta + theta_offset
            x = np.cos(angle) * radius + center.x
            y = np.sin(angle) * radius + center.y
            z = center.z
            wp = Waypoint(x, y, z, max_forward_speed, heading_offset)
            self.add_waypoint(wp)
        return True

    def generate_helix(
        self,
        radius,
        center,
        num_points,
        max_forward_speed,
        delta_z,
        num_turns,
        theta_offset=0.0,
        heading_offset=0.0,
        append=False,
    ):
        """Generate a set of waypoints describing a helix

        > *Input arguments*

        * `radius` (*type:* `float`): Radius of the circle in meters
        * `num_points` (*type:* `int`): Number of waypoints to be generated
        * `max_forward_speed` (*type:* `float`): Max. forward speed set to each waypoint in m/s
        * `delta_z` (*type:* `float`): Step in the Z direction for each lap of the helix in meters
        * `theta_offset` (*type:* `float`, *default:* `0`): Angle offset to start generating the waypoints in radians
        * `heading_offset` (*type:* `float`, *default:* `0`): Heading offset set to the reference heading of the vehicle in radians
        * `append` (*type:* `bool`, *default:* `False`): If `True`, append the generated waypoints to the existent waypoints in the set

        > *Returns*

        `True` if the circle was successfully generated, `False`, otherwise
        """
        if radius <= 0:
            print("Invalid radius, value={}".format(radius))
            return False

        if num_points <= 0:
            print("Invalid number of samples, value={}".format(num_points))
            return False

        if num_turns <= 0:
            print("Invalid number of turns, value={}".format(num_points))
            return False

        if max_forward_speed <= 0:
            print(
                "Invalid absolute maximum velocity, value={}".format(max_forward_speed)
            )
            return False

        if not append:
            # Clear current list
            self.clear_waypoints()

        total_angle = 2 * np.pi * num_turns
        step_angle = total_angle / num_points
        step_z = float(delta_z) / num_points
        for i in range(num_points):
            angle = theta_offset + i * step_angle
            x = radius * np.cos(angle) + center.x
            y = radius * np.sin(angle) + center.y
            z = step_z * i + center.z

            wp = Waypoint(x, y, z, max_forward_speed, heading_offset)
            self.add_waypoint(wp)
        return True
