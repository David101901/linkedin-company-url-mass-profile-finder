thonimport csv
import json
import logging
import os
from typing import List, Dict, Any
from xml.etree.ElementTree import Element, SubElement, ElementTree

import pandas as pd

def _ensure_dir(path: str) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)

def export_json(records: List[Dict[str, Any]], path: str) -> None:
    _ensure_dir(path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        logging.info("JSON exported to %s (%d records)", path, len(records))
    except OSError as exc:
        logging.error("Failed to write JSON to %s: %s", path, exc)
        raise

def export_csv(records: List[Dict[str, Any]], path: str) -> None:
    if not records:
        logging.warning("No records to write to CSV. Skipping.")
        return

    _ensure_dir(path)

    fieldnames = sorted({key for record in records for key in record.keys()})

    try:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        logging.info("CSV exported to %s (%d records)", path, len(records))
    except OSError as exc:
        logging.error("Failed to write CSV to %s: %s", path, exc)
        raise

def export_excel(records: List[Dict[str, Any]], path: str) -> None:
    if not records:
        logging.warning("No records to write to Excel. Skipping.")
        return

    _ensure_dir(path)

    df = pd.DataFrame(records)
    try:
        df.to_excel(path, index=False)
        logging.info("Excel exported to %s (%d records)", path, len(records))
    except Exception as exc:
        logging.error("Failed to write Excel to %s: %s", path, exc)
        raise

def export_xml(records: List[Dict[str, Any]], path: str) -> None:
    _ensure_dir(path)

    root = Element("companies")
    for record in records:
        company_el = SubElement(root, "company")
        for key, value in record.items():
            child = SubElement(company_el, key)
            child.text = "" if value is None else str(value)

    tree = ElementTree(root)
    try:
        tree.write(path, encoding="utf-8", xml_declaration=True)
        logging.info("XML exported to %s (%d records)", path, len(records))
    except OSError as exc:
        logging.error("Failed to write XML to %s: %s", path, exc)
        raise

def export_rss(records: List[Dict[str, Any]], path: str) -> None:
    """
    Export records as a simple RSS 2.0 feed where each item represents a company.
    """
    _ensure_dir(path)

    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    title = SubElement(channel, "title")
    title.text = "LinkedIn Company URL Results"

    link = SubElement(channel, "link")
    link.text = "https://example.com/linkedin-company-url-feed"

    description = SubElement(channel, "description")
    description.text = "Feed containing LinkedIn company profile URLs discovered by the scraper."

    for record in records:
        item = SubElement(channel, "item")

        item_title = SubElement(item, "title")
        company_name = record.get("companyName") or "Unknown Company"
        item_title.text = company_name

        item_link = SubElement(item, "link")
        linkedin_url = record.get("linkedinUrl")
        if linkedin_url:
            item_link.text = str(linkedin_url)
        else:
            item_link.text = "https://www.linkedin.com/"

        item_description = SubElement(item, "description")
        status = record.get("infoStatus") or "Unknown"
        search_query = record.get("searchQuery") or ""
        item_description.text = f"Status: {status}. Query: {search_query}"

    tree = ElementTree(rss)
    try:
        tree.write(path, encoding="utf-8", xml_declaration=True)
        logging.info("RSS exported to %s (%d records)", path, len(records))
    except OSError as exc:
        logging.error("Failed to write RSS to %s: %s", path, exc)
        raise