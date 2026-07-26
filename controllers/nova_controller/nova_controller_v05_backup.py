"""NOVA v0.5: Autonomous rescue mission with colour target detection."""

from controller import Robot
import random


# -------------------------------------------------------------------
# BASIC SETTINGS
# -------------------------------------------------------------------

TIME_STEP = 64

FORWARD_SPEED = 3.0
TURN_SPEED = 2.5
REVERSE_SPEED = 2.0

OBSTACLE_THRESHOLD = 80.0
TURN_DURATION = 14
TRAPPED_TURN_DURATION = 22
REVERSE_DURATION = 12

# Process every second pixel to reduce camera-processing workload.
PIXEL_STEP = 2

# 0.015 means 1.5% of sampled pixels.
COLOUR_RATIO_THRESHOLD = 0.015


# -------------------------------------------------------------------
# ROBOT INITIALIZATION
# -------------------------------------------------------------------

robot = Robot()

left_motor = robot.getDevice("left wheel motor")
right_motor = robot.getDevice("right wheel motor")

left_motor.setPosition(float("inf"))
right_motor.setPosition(float("inf"))

left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)


# -------------------------------------------------------------------
# PROXIMITY SENSOR INITIALIZATION
# -------------------------------------------------------------------

proximity_sensors = []

for sensor_number in range(8):
    sensor = robot.getDevice(f"ps{sensor_number}")
    sensor.enable(TIME_STEP)
    proximity_sensors.append(sensor)


# -------------------------------------------------------------------
# CAMERA INITIALIZATION
# -------------------------------------------------------------------

camera = robot.getDevice("camera")
camera.enable(TIME_STEP)

camera_width = camera.getWidth()
camera_height = camera.getHeight()


# -------------------------------------------------------------------
# MISSION VARIABLES
# -------------------------------------------------------------------

found_targets: set[str] = set()

required_targets = {
    "RED",
    "GREEN",
    "BLUE",
}

turn_steps_remaining = 0
reverse_steps_remaining = 0
turn_direction = "left"

camera_check_counter = 0


print("================================================")
print("NOVA v0.5 RESCUE MISSION STARTED")
print("Autonomous navigation: ENABLED")
print("Camera colour detection: ENABLED")
print("Stuck escape system: ENABLED")
print("Targets required: RED, GREEN and BLUE")
print("================================================")


# -------------------------------------------------------------------
# COLOUR DETECTION FUNCTION
# -------------------------------------------------------------------

def detect_target_colours() -> set[str]:
    """Return rescue-target colours currently visible to the camera."""

    image = camera.getImage()

    if image is None:
        return set()

    red_pixels = 0
    green_pixels = 0
    blue_pixels = 0
    sampled_pixels = 0

    for y in range(0, camera_height, PIXEL_STEP):
        for x in range(0, camera_width, PIXEL_STEP):
            red = camera.imageGetRed(image, camera_width, x, y)
            green = camera.imageGetGreen(image, camera_width, x, y)
            blue = camera.imageGetBlue(image, camera_width, x, y)

            sampled_pixels += 1

            if (
                red > 140
                and red > green * 1.5
                and red > blue * 1.5
            ):
                red_pixels += 1

            elif (
                green > 140
                and green > red * 1.5
                and green > blue * 1.5
            ):
                green_pixels += 1

            elif (
                blue > 140
                and blue > red * 1.5
                and blue > green * 1.5
            ):
                blue_pixels += 1

    if sampled_pixels == 0:
        return set()

    red_ratio = red_pixels / sampled_pixels
    green_ratio = green_pixels / sampled_pixels
    blue_ratio = blue_pixels / sampled_pixels

    visible_colours: set[str] = set()

    if red_ratio >= COLOUR_RATIO_THRESHOLD:
        visible_colours.add("RED")

    if green_ratio >= COLOUR_RATIO_THRESHOLD:
        visible_colours.add("GREEN")

    if blue_ratio >= COLOUR_RATIO_THRESHOLD:
        visible_colours.add("BLUE")

    return visible_colours


# -------------------------------------------------------------------
# MAIN CONTROL LOOP
# -------------------------------------------------------------------

while robot.step(TIME_STEP) != -1:
    sensor_values = [
        sensor.getValue()
        for sensor in proximity_sensors
    ]

    front_left = max(
        sensor_values[5],
        sensor_values[6],
        sensor_values[7],
    )

    front_right = max(
        sensor_values[0],
        sensor_values[1],
        sensor_values[2],
    )

    obstacle_ahead = (
        front_left > OBSTACLE_THRESHOLD
        or front_right > OBSTACLE_THRESHOLD
    )

    both_sides_blocked = (
        front_left > OBSTACLE_THRESHOLD
        and front_right > OBSTACLE_THRESHOLD
    )

    # ---------------------------------------------------------------
    # CAMERA TARGET CHECK
    # ---------------------------------------------------------------

    camera_check_counter += 1

    if camera_check_counter >= 5:
        camera_check_counter = 0

        visible_targets = detect_target_colours()

        for target_colour in visible_targets:
            if target_colour not in found_targets:
                found_targets.add(target_colour)

                print("")
                print("*************************************")
                print(f"TARGET FOUND: {target_colour}")
                print(
                    f"Mission progress: "
                    f"{len(found_targets)}/{len(required_targets)}"
                )
                print("*************************************")
                print("")

        if found_targets == required_targets:
            left_motor.setVelocity(0.0)
            right_motor.setVelocity(0.0)

            print("")
            print("========================================")
            print("MISSION COMPLETE")
            print("ALL 3 RESCUE TARGETS HAVE BEEN LOCATED")
            print("NOVA HAS STOPPED")
            print("========================================")

            break

    # ---------------------------------------------------------------
    # AUTONOMOUS NAVIGATION WITH STUCK ESCAPE
    # ---------------------------------------------------------------

    left_speed = 0.0
    right_speed = 0.0

    # Reverse when trapped.
    if reverse_steps_remaining > 0:
        left_speed = -REVERSE_SPEED
        right_speed = -REVERSE_SPEED
        reverse_steps_remaining -= 1

    # Continue an existing turn.
    elif turn_steps_remaining > 0:
        if turn_direction == "left":
            left_speed = -TURN_SPEED
            right_speed = TURN_SPEED
        else:
            left_speed = TURN_SPEED
            right_speed = -TURN_SPEED

        turn_steps_remaining -= 1

    # Escape if both front sides are blocked.
    elif both_sides_blocked:
        reverse_steps_remaining = REVERSE_DURATION
        turn_steps_remaining = TRAPPED_TURN_DURATION
        turn_direction = random.choice(["left", "right"])

        left_speed = -REVERSE_SPEED
        right_speed = -REVERSE_SPEED

        print(
            "NOVA IS TRAPPED — REVERSING | "
            f"Next turn: {turn_direction}"
        )

    # Normal obstacle response.
    elif obstacle_ahead:
        if front_left > front_right:
            turn_direction = "right"
        elif front_right > front_left:
            turn_direction = "left"
        else:
            turn_direction = random.choice(["left", "right"])

        turn_steps_remaining = TURN_DURATION

        left_speed = 0.0
        right_speed = 0.0

        print(
            f"Obstacle detected | "
            f"Left: {front_left:.1f} | "
            f"Right: {front_right:.1f} | "
            f"Turning {turn_direction}"
        )

    # Clear path.
    else:
        left_speed = FORWARD_SPEED
        right_speed = FORWARD_SPEED

    # These lines are essential: they actually move the wheels.
    left_motor.setVelocity(left_speed)
    right_motor.setVelocity(right_speed)