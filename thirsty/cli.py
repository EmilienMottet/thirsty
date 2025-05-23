import argparse

import gpxpy
import rich.console
import rich.progress

import thirsty.core

console = rich.console.Console()


def main():
    default_water = next(iter(thirsty.core.WATER_AMENITIES))
    default_toilet = next(iter(thirsty.core.TOILET_AMENITIES))
    default_repair = next(iter(thirsty.core.REPAIR_AMENITIES))
    default_food = next(iter(thirsty.core.FOOD_AMENITIES))

    parser = argparse.ArgumentParser(description="Add water, toilet, bicycle repair, and food POIs to a GPX trace.")

    parser.add_argument("input", help="input GPX trace")

    parser.add_argument("output", help="output GPX trace",
                        type=argparse.FileType("w"))

    parser.add_argument("-d", "--distance", type=float, default=100,
                        help="default search distance around trace (in meters)")
                        
    parser.add_argument("--water-distance", type=float, default=None,
                        help="search distance for water points (in meters)")
                        
    parser.add_argument("--toilet-distance", type=float, default=None,
                        help="search distance for toilets (in meters)")
                        
    parser.add_argument("--repair-distance", type=float, default=None,
                        help="search distance for repair stations (in meters)")
                        
    parser.add_argument("--food-distance", type=float, default=None,
                        help="search distance for food amenities (in meters)")

    parser.add_argument("--html", action="store_true",
                        help="generate HTML interactive map to <output>.html")

    parser.add_argument("-w", "--water", action="append",
                        choices=thirsty.core.WATER_AMENITIES.keys(), default=None,
                        help=f"set which type of water amenities to consider (default: {default_water})")
                        
    parser.add_argument("-t", "--toilet", action="store_true",
                        help="add toilet amenities to the trace")
                        
    parser.add_argument("-r", "--repair", action="append",
                        choices=thirsty.core.REPAIR_AMENITIES.keys(), default=None,
                        help=f"add bicycle repair amenities to the trace (can be repeated)")
                        
    parser.add_argument("-f", "--food", action="append",
                        choices=thirsty.core.FOOD_AMENITIES.keys(), default=None,
                        help=f"add food and refreshment amenities to the trace (can be repeated)")

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
            
    # No default options anymore - user must explicitly select water amenities
    
    toilet_types = []
    if args.toilet:
        toilet_types = [default_toilet]
        
    repair_types = args.repair
    
    food_types = args.food

    if args.water:
        console.print(f"Selected water amenities: {args.water}")
    else:
        console.print("No water amenities selected")
        
    if args.toilet:
        console.print(f"Selected toilet amenities: {toilet_types}")
    else:
        console.print("No toilet amenities selected")
        
    if repair_types:
        console.print(f"Selected repair amenities: {repair_types}")
    else:
        console.print("No repair amenities selected")
        
    if food_types:
        console.print(f"Selected food amenities: {food_types}")
    else:
        console.print("No food amenities selected")

    gpx = gpxpy.parse(input)
    bounds = thirsty.core.get_bounds(gpx)
    pois = thirsty.core.query_overpass(bounds, args.water, toilet_types, repair_types, food_types)
    
    # Set up type-specific distances
    type_distances = {}
    if args.water_distance is not None:
        type_distances["WATER"] = args.water_distance
    if args.toilet_distance is not None:
        type_distances["TOILET"] = args.toilet_distance
    if args.repair_distance is not None:
        type_distances["GEAR"] = args.repair_distance
    if args.food_distance is not None:
        type_distances["FOOD"] = args.food_distance
        
    pois = thirsty.core.filter_pois_near_track(gpx, pois, max_distance_m=args.distance, type_distances=type_distances)
    gpx = thirsty.core.add_waypoints_to_gpx(gpx, pois)

    if args.html:
        map = thirsty.core.display_gpx_on_map(gpx, pois)
        map.save(args.output.name + ".html")

    gpx = thirsty.core.sanitize_gpx_text(gpx.to_xml())

    args.output.write(gpx)

    console.print(f"✅ Added {len(pois)} POI to {args.output.name}")
