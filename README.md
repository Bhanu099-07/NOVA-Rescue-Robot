\# NOVA Rescue Robot



NOVA is an autonomous simulated rescue robot built using Python and Webots.



It explores an enclosed environment, avoids obstacles, detects colour-coded rescue targets using its onboard camera, tracks mission progress, and stops automatically after completing its mission.



!\[NOVA Rescue Mission](media/nova\_mission\_complete.png)



\## Demo



Watch the full NOVA v0.5 autonomous rescue mission here:



\[View the NOVA v0.5 Release](https://github.com/Bhanu099-07/NOVA-Rescue-Robot/releases/tag/v0.5.0)



\## Mission Objective



NOVA must autonomously locate three rescue targets:



\- Red

\- Green

\- Blue



Once all three targets are detected, the robot stops and reports that the mission is complete.



\## Features



\- Autonomous movement

\- Eight infrared proximity sensors

\- Wall and obstacle avoidance

\- Direction selection using sensor readings

\- Reverse escape behaviour when trapped

\- Camera-based colour detection

\- Red, green, and blue target recognition

\- Duplicate-target prevention

\- Mission progress tracking

\- Automatic mission completion



\## Technologies Used



\- Python

\- Webots

\- Computer vision

\- Robot proximity sensors

\- Git

\- GitHub



\## How NOVA Works



NOVA continuously reads the E-puck robot's proximity sensors.



When the path is clear, it moves forward. When an obstacle is detected, it compares the sensor readings on the left and right sides and turns toward the clearer direction.



If NOVA becomes trapped, it reverses before making a larger turn.



The onboard camera scans pixels for dominant red, green, and blue regions. Each target colour is counted only once.



\## Project Structure



```text

NOVA-Rescue-Robot/

├── controllers/

│   └── nova\_controller/

│       ├── nova\_controller.py

│       ├── nova\_controller\_v03\_backup.py

│       └── nova\_controller\_v04\_backup.py

├── worlds/

│   └── nova\_test\_arena.wbt

├── media/

│   └── nova\_mission\_complete.png

├── .gitignore

└── README.md

