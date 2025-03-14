Choplifter Clone

A Python-based clone of the classic Commodore 64 game Choplifter built using Pygame. This project recreates the authentic 8-bit gameplay experience with modern development practices, featuring smooth helicopter controls, directional shooting, rescue mechanics, enemy tanks, and explosion effects.
Overview

Inspired by the original Choplifter, this project uses a low-resolution virtual display (320×200) that scales to modern resolutions. It combines classic C64 aesthetics with modern game mechanics and a modular codebase to create an engaging rescue mission game.
Key Features

    Retro Visuals: Emulates C64-style graphics with a scaled-up, modern display.
    Helicopter Mechanics: Enjoy 8-directional movement with inertia, rotor animations, landing detection, and rescue capabilities.
    Combat & Rescue: Fire projectiles at enemy tanks, pick up hostages, and drop them off in designated zones.
    Modular Design: Easily extendable architecture for adding enemy AI, procedural level generation, advanced physics, and more.

Installation
Requirements

    Python 3.x
    Pygame (tested with version 2.x)

Setup Instructions

    Clone the repository:

git clone https://github.com/yourusername/choplifter-clone.git
cd choplifter-clone

Create and activate a virtual environment (optional but recommended):

python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

Install the required packages:

pip install -r requirements.txt

Run the game:

    python main.py

How to Play

    Arrow Keys: Control the helicopter’s movement
        Left/Right: Steer and initiate turning animations
        Up: Increase lift/ascend
    Space Bar: Fire projectiles
    D Key: (For testing) Inflict damage to the helicopter
    T Key: Take off from the ground (after landing)
    Escape Key: Quit the game

Objective: Rescue as many hostages as possible while avoiding enemy tanks and managing your helicopter's health.
Development Roadmap

    Phase 1: Core Framework
        Set up game loop with delta-time calculation and input handling.
        Implement a virtual camera and parallax background system.
    Phase 2: Combat Systems
        Develop enemy AI state machines and projectile pooling.
        Integrate damage calculations and improved collision detection.
    Phase 3: Rescue & Level Design
        Add procedural bunker placement and XML-based level definitions.
        Implement hostage rescue logic with pathfinding algorithms.
    Phase 4: Polish & Optimization
        Optimize rendering (dirty rectangle rendering).
        Integrate advanced sound effects (using SFXR-py) and a save system.
        Fine-tune authentic flight physics and add performance benchmarks.

Contributing

Contributions are welcome! Feel free to fork the repository, make improvements, and open pull requests. For issues or feature requests, please use the GitHub Issues page.
License

This project is licensed under the MIT License.
Acknowledgements

    Inspired by the classic Choplifter game for the Commodore 64.
    Developed with Pygame and modern Python libraries.

Enjoy the game and happy rescuing!
