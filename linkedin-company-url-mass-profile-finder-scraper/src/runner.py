thonimport argparse
import json
import logging
import os
import sys
from typing import List, Dict, Any

# Ensure src directory is on sys.path so namespace packages work
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from extractors.linkedin_finder import LinkedInFinder
from outputs.exporters import (
    export_json,
    export_csv,
    export_excel,
    export_xml,
    export_rss,
)

def load_settings(config_path: str) -> Dict[str, Any]:
    """
    Load settings from JSON file. If the file is missing or invalid,
    sensible defaults are returned.
    """
    default_settings = {
        "search_engine": "bing",
        "request_timeout": 10,
        "user_agent": "LinkedInCompanyFinderBot/1.0",
        "output_formats": ["json"],
        "input_file": "data/company_list.sample.txt",
        "output_dir": "data",
    }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                logging.warning("Config file does not contain a JSON object. Using defaults.")
                return default_settings
            default_settings.update(data)
    except FileNotFoundError:
        logging.info("Config file %s not found. Using defaults.", config_path)
    except json.JSONDecodeError as exc:
        logging.warning("Failed to parse config file %s: %s. Using defaults.", config_path, exc)

    return default_settings

def read_company_list(path: str) -> List[str]:
    """
    Read company names from a text file. Skips empty lines and comments (#).
    """
    companies: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if not name or name.startswith("#"):
                    continue
                companies.append(name)
    except FileNotFoundError:
        logging.error("Input file %s not found.", path)
        raise
    except OSError as exc:
        logging.error("Error reading input file %s: %s", path, exc)
        raise

    if not companies:
        logging.warning("No companies found in %s.", path)
    return companies

def collect_results(
    companies: List[str],
    finder: LinkedInFinder,
) -> List[Dict[str, Any]]:
    """
    For each company, query the finder and collect normalized results.
    """
    results: List[Dict[str, Any]] = []
    for company in companies:
        try:
            result = finder.find_company_profile(company_name=company)
        except Exception as exc:
            logging.exception("Unexpected error while processing '%s': %s", company, exc)
            result = {
                "companyName": company,
                "searchQuery": f"linkedin {company}",
                "linkedinUrl": None,
                "infoStatus": "Error",
            }
        results.append(result)
    return results

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LinkedIn Company URL - Mass Profile Finder"
    )
    parser.add_argument(
        "--config",
        default=os.path.join(CURRENT_DIR, "config", "settings.example.json"),
        help="Path to JSON configuration file (default: settings.example.json)",
    )
    parser.add_argument(
        "--input",
        help="Path to input file containing company names (one per line). "
             "Overrides the config file if supplied.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to write output files to. Overrides the config value if supplied.",
    )
    parser.add_argument(
        "--formats",
        help="Comma-separated list of output formats: json,csv,excel,xml,rss. "
             "Overrides the config file if supplied.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    settings = load_settings(args.config)

    input_file = args.input or settings["input_file"]
    output_dir = args.output_dir or settings["output_dir"]

    if args.formats:
        output_formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    else:
        output_formats = [f.lower() for f in settings.get("output_formats", ["json"])]

    valid_formats = {"json", "csv", "excel", "xml", "rss"}
    invalid = [f for f in output_formats if f not in valid_formats]
    if invalid:
        logging.warning(
            "Ignoring invalid formats: %s. Valid options are: %s",
            ", ".join(invalid),
            ", ".join(sorted(valid_formats)),
        )
    output_formats = [f for f in output_formats if f in valid_formats]
    if not output_formats:
        logging.error("No valid output formats specified.")
        sys.exit(1)

    companies = read_company_list(input_file)
    if not companies:
        logging.error("No company names to process. Exiting.")
        sys.exit(1)

    finder = LinkedInFinder(
        search_engine=settings.get("search_engine", "bing"),
        timeout=settings.get("request_timeout", 10),
        user_agent=settings.get("user_agent", "LinkedInCompanyFinderBot/1.0"),
    )

    logging.info("Starting lookup for %d companies.", len(companies))
    results = collect_results(companies, finder)
    logging.info("Lookup finished. %d records collected.", len(results))

    os.makedirs(output_dir, exist_ok=True)

    base_name = "linkedin_company_urls"
    if "json" in output_formats:
        path = os.path.join(output_dir, f"{base_name}.json")
        export_json(results, path)
    if "csv" in output_formats:
        path = os.path.join(output_dir, f"{base_name}.csv")
        export_csv(results, path)
    if "excel" in output_formats:
        path = os.path.join(output_dir, f"{base_name}.xlsx")
        export_excel(results, path)
    if "xml" in output_formats:
        path = os.path.join(output_dir, f"{base_name}.xml")
        export_xml(results, path)
    if "rss" in output_formats:
        path = os.path.join(output_dir, f"{base_name}.rss.xml")
        export_rss(results, path)

    logging.info("All done. Outputs written to %s", os.path.abspath(output_dir))

if __name__ == "__main__":
    main()