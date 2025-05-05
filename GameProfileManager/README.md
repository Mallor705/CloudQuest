# Game Profile Manager

## Overview
Game Profile Manager is a command-line application designed to help users manage game profiles for various games. It allows users to create, load, and save profiles with specific configurations, making it easier to switch between different game settings.

## Features
- Create new game profiles with `--newgame`
- Load existing profiles using `--config`
- Support for specific game profiles such as `--eldenring` and `--darksouls`
- Easy command-line interface for managing game settings

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd GameProfileManager
   ```
3. Build the project:
   ```
   dotnet build
   ```

## Usage
To use the Game Profile Manager, run the executable with the desired command-line options. Here are some examples:

- Create a new profile for Elden Ring:
  ```
  GameProfileManager --newgame --eldenring
  ```

- Load a specific configuration:
  ```
  GameProfileManager --config path/to/config.json
  ```

- Manage profiles for Dark Souls:
  ```
  GameProfileManager --darksouls
  ```

## Command-Line Options
- `--newgame`: Create a new game profile.
- `--config <path>`: Load a specific configuration file.
- `--eldenring`: Use the profile settings for Elden Ring.
- `--darksouls`: Use the profile settings for Dark Souls.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.