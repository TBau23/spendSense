"""
Content Catalog Loader

Loads educational content, partner offers, and generic templates into SQLite database.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from .storage import (
    insert_content_catalog_item,
    insert_partner_offer,
    insert_generic_template
)


def load_content_catalog_from_json(db_path: str, json_path: str) -> int:
    """
    Load educational content catalog from JSON file into database.
    
    Args:
        db_path: Path to SQLite database
        json_path: Path to content_catalog.json
    
    Returns:
        Number of items loaded
    """
    with open(json_path, 'r') as f:
        content_items = json.load(f)
    
    for item in content_items:
        insert_content_catalog_item(db_path, item)
    
    print(f"✓ Loaded {len(content_items)} educational content items")
    return len(content_items)


def load_partner_offers_from_json(db_path: str, json_path: str) -> int:
    """
    Load partner offers catalog from JSON file into database.
    
    Args:
        db_path: Path to SQLite database
        json_path: Path to partner_offers.json
    
    Returns:
        Number of offers loaded
    """
    with open(json_path, 'r') as f:
        offers = json.load(f)
    
    for offer in offers:
        insert_partner_offer(db_path, offer)
    
    print(f"✓ Loaded {len(offers)} partner offers")
    return len(offers)


def load_generic_templates_from_json(db_path: str, json_path: str) -> int:
    """
    Load generic templates from JSON file into database.
    
    Args:
        db_path: Path to SQLite database
        json_path: Path to generic_templates.json
    
    Returns:
        Number of templates loaded
    """
    with open(json_path, 'r') as f:
        templates = json.load(f)
    
    for template in templates:
        insert_generic_template(db_path, template)
    
    print(f"✓ Loaded {len(templates)} generic templates")
    return len(templates)


def load_all_catalogs(db_path: str, catalog_dir: str):
    """
    Load all catalogs from a directory into database.
    
    Args:
        db_path: Path to SQLite database
        catalog_dir: Directory containing JSON catalog files
    """
    catalog_path = Path(catalog_dir)
    
    # Load content catalog
    content_file = catalog_path / 'content_catalog.json'
    if content_file.exists():
        load_content_catalog_from_json(db_path, str(content_file))
    else:
        print(f"⚠ Content catalog not found: {content_file}")
    
    # Load partner offers
    offers_file = catalog_path / 'partner_offers.json'
    if offers_file.exists():
        load_partner_offers_from_json(db_path, str(offers_file))
    else:
        print(f"⚠ Partner offers not found: {offers_file}")
    
    # Load generic templates
    templates_file = catalog_path / 'generic_templates.json'
    if templates_file.exists():
        load_generic_templates_from_json(db_path, str(templates_file))
    else:
        print(f"⚠ Generic templates not found: {templates_file}")

