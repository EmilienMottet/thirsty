[![GitHub stars](https://img.shields.io/github/stars/jsleroy/thirsty.svg?style=social)](https://github.com/jsleroy/thirsty/stargazers)

<p align="center">
<img src="docs/assets/logo.png" alt="Thirsty Logo" width="200"/>
</p>

# Thirsty

Add hydration points, toilets, and bicycle repair stations to your GPX tracks automatically 🚴‍♂️💧🚻🔧

<p align="center">
<a href="https://www.paypal.com/donate/?business=TJAXC3T4WD66L&no_recurring=0&currency_code=EUR" target="_blank">
<img src="https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge" alt="Donate with PayPal"/>
</a>
</p>

Thirsty is a Python tool that enhances your GPX files by adding Points of Interest (POIs), such as drinking water points, toilets, and bicycle repair stations, to your cycling or running routes. It integrates with the Overpass API to query OpenStreetMap for relevant points along your route and adds them to the GPX file. Ideal for long-distance cycling events, ultra races, or any activity where hydration points and facilities matter!

Found a bug? Need a new feature? [Open an Issue](https://github.com/jsleroy/thirsty/issues)!

## 📷 Screenshots

### Add Water Points to Your GPX

<p align="center">
<img src="docs/assets/before-after.png" alt="Before" width="80%"/>
</p>

### Visualize on a Map

<p align="center">
<img src="docs/assets/map.png" alt="Map Display" width="80%"/>
</p>

### Simple Command-Line Interface

<p align="center">
<img src="docs/assets/terminal.png" alt="Terminal Usage" width="80%"/>
</p>

## Features

- **Query Overpass API**: Fetch drinking water, toilet, and bicycle repair POIs from OpenStreetMap.
- **Bounding Box Filtering**: Filter POIs around a defined area to match your GPX route.
- **Distance-based Filtering**: Ensures POIs are within a defined proximity of your GPX track.
- **Supports GPX from URL and Local Files**: Easily work with GPX files from your device or download them from a URL.
- **In-Memory Handling**: No need for temporary files; everything is handled in memory for speed.
- **Progress Bar**: Monitor download and processing progress with the `rich` module.

## POI Type Selection

By default, **Thirsty** searches for public drinking water fountains (`drinking_water` POIs).
You can customize which types of POIs you want to add using the following options:

- **`--water`** (or `-w`): Specify water-related POI types (can be repeated for multiple types)
- **`--toilet`** (or `-t`): Add toilet amenities to the trace (flag, no additional argument needed)
- **`--repair`** (or `-r`): Specify bicycle repair-related POI types (can be repeated for multiple types)

If no option is specified, the default water amenity (`drinking_water`) will be used.

### Available POI types

#### Water Amenities

| POI Type        | Description                                                            |
|:----------------|:-----------------------------------------------------------------------|
| `water`         | Public drinking water fountains (default).                            |
| `point`         | Water refill stations for caravans, RVs, or marinas (only potable ones). |
| `tap`           | Taps providing potable water.                                          |
| `spring`        | Natural springs with potable water.                                   |
| `fountain`      | Public decorative fountains explicitly marked as potable.             |

#### Toilet Amenities

| POI Type        | Description                                                            |
|:----------------|:-----------------------------------------------------------------------|
| `toilets`       | Public toilets.                                                       |

#### Repair Amenities

| POI Type        | Description                                                            |
|:----------------|:-----------------------------------------------------------------------|
| `workshop`      | Dedicated bicycle repair stations.                                    |
| `rental`        | Bicycle rental stations that also offer repair services.              |
| `pump`          | Compressed air stations (for tires).                                  |
| `shop`          | Bicycle shops that offer repair services.                             |

### Example usage

Use default drinking water points:

```bash
thirsty input.gpx output.gpx
```

Use **only** springs and water taps:

```bash
thirsty input.gpx output.gpx -w spring -w tap
```

Add both water points and toilets:

```bash
thirsty input.gpx output.gpx -w water -t
```

Add water points, toilets, and bicycle repair stations:

```bash
thirsty input.gpx output.gpx -w water -t -r workshop -r pump
```

Add all supported water amenities, toilets, and bicycle repair amenities:

```bash
thirsty input.gpx output.gpx -w water -w point -w tap -w spring -w fountain -t -r workshop -r rental -r pump -r shop
```

> **Note**: The older `-p` option is still supported for backward compatibility but is deprecated. It is recommended to use the `-w` option instead.

## ⚙️ Installation

Clone this repository and set up a virtual environment:

```bash
git clone https://github.com/jsleroy/thirsty
cd thirsty
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
pip install .
```

## Usage

### Download GPX from URL and Add POIs

This example shows how to download a GPX file from a URL, add drinking water, toilet, and bicycle repair POIs to the route, and save the modified GPX to an output file.

```bash
thirsty https://example.com/yourfile.gpx output.gpx --water water --toilet --repair workshop --distance 150
```

- **URL or Local GPX**: Supports both local files and downloading from a URL.
- **Water Amenities**: Specify which water amenities to add with `-w/--water`.
- **Toilet Amenities**: Add toilets with `-t/--toilet`.
- **Repair Amenities**: Specify which bicycle repair amenities to add with `-r/--repair`.
- **Distance**: Optionally specify the maximum distance (in meters) from the track for POIs (default: 100 meters).

### Local GPX File Usage

You can also process a local GPX file with various options:

```bash
# Add default water points
thirsty input.gpx output.gpx

# Add water points and toilets
thirsty input.gpx output.gpx -w water -t

# Add water points, toilets, and bicycle repair stations
thirsty input.gpx output.gpx -w water -t -r workshop

# Specify search distance
thirsty input.gpx output.gpx -w water -t -r workshop --distance 150
```

### Features in Detail

#### 1. Bounding Box Filtering
- Queries the Overpass API for drinking water, toilet, and bicycle repair POIs within the bounding box of the GPX file's route.

#### 2. Distance-based Filtering
- Filters POIs that are within a specified distance from the GPX track. This ensures that only nearby POIs are added to the GPX file.

#### 3. In-Memory File Handling
- Both downloaded and local GPX files are handled entirely in memory, eliminating the need for temporary files and speeding up the process.

#### 4. Progress Bar
- During the download process, the script shows a progress bar (using the `rich` library) so you can track the download status in real-time.

## ️ Development

### Requirements

- Python 3.7+
- `requests`: For HTTP requests to Overpass API and downloading GPX files.
- `gpxpy`: For reading and writing GPX files.
- `rich`: For the progress bar and rich text output.

### Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Running the CLI

You can run the script directly from the command line. Make sure to provide the appropriate input parameters (either a local file or a URL) and specify the output file:

```bash
thirsty input.gpx output.gpx --distance 150
```

## Contributing

1. Fork this repository and create a new branch.
2. Make your changes and commit them.
3. Push your changes to your fork.
4. Create a Pull Request with a detailed description of your changes.

## License

This project is licensed under the [GNU GPL v3 License](LICENSE).
