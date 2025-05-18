import argparse

import gpxpy
import rich.console
import rich.progress

import thirsty.core

console = rich.console.Console()


def main():
    default_water = next(iter(thirsty.core.WATER_AMENITIES))
    default_toilet = next(iter(thirsty.core.TOILET_AMENITIES))

    parser = argparse.ArgumentParser(description="Add water and toilet POIs to a GPX trace.")

    parser.add_argument("input", help="input GPX trace")

    parser.add_argument("output", help="output GPX trace",
                        type=argparse.FileType("w"))

    parser.add_argument("-d", "--distance", type=float, default=100,
                        help="search distance around trace")

    parser.add_argument("--html", action="store_true",
                        help="generate HTML interactive map to <output>.html")

    parser.add_argument("-w", "--water", action="append",
                        choices=thirsty.core.WATER_AMENITIES.keys(), default=None,
                        help=f"set which type of water amenities to consider (default: {default_water})")
                        
    parser.add_argument("-t", "--toilet", action="store_true",
                        help="add toilet amenities to the trace")

    # Keep backward compatibility with -p argument
    parser.add_argument("-p", "--poi-type", action="append",
                        choices=thirsty.core.WATER_AMENITIES.keys(), default=None,
                        help=f"DEPRECATED: use -w instead")

    args = parser.parse_args()

    if args.input.startswith("http"):
        input = thirsty.core.download_gpx(args.input)
    else:
        input = open(args.input, "rb") # noqa: SIM115

    # Handle backward compatibility
    if args.poi_type is not None:
        if args.water is None:
            args.water = args.poi_type
        else:
            args.water.extend(args.poi_type)
            
    # Set defaults if no options provided
    if args.water is None:
        args.water = [default_water]
        
    toilet_types = []
    if args.toilet:
        toilet_types = [default_toilet]

    console.print(f"Selected water amenities: {args.water}")
    if args.toilet:
        console.print(f"Selected toilet amenities: {toilet_types}")
    else:
        console.print("No toilet amenities selected")

    gpx = gpxpy.parse(input)
    bounds = thirsty.core.get_bounds(gpx)
    pois = thirsty.core.query_overpass(bounds, args.water, toilet_types)
    pois = thirsty.core.filter_pois_near_track(gpx, pois, max_distance_m=args.distance)
    gpx = thirsty.core.add_waypoints_to_gpx(gpx, pois)

    if args.html:
        map = thirsty.core.display_gpx_on_map(gpx, pois)
        map.save(args.output.name + ".html")

    gpx = thirsty.core.sanitize_gpx_text(gpx.to_xml())

    args.output.write(gpx)

    console.print(f"✅ Added {len(pois)} POI to {args.output.name}")
