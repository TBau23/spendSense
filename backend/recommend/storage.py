"""
Recommendation Storage

Handles SQLite and Parquet storage for recommendations, content catalog,
partner offers, and generic templates.
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime


def create_recommendation_tables(db_path: str):
    """
    Create all recommendation-related tables in SQLite database.
    
    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Recommendations table (parent record per user)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            window_30d_persona_id INTEGER,
            window_180d_persona_id INTEGER,
            target_personas TEXT,  -- JSON array of targeted persona IDs
            
            -- Metadata
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            llm_model TEXT,
            generation_latency_seconds REAL,
            
            -- Counts
            educational_item_count INTEGER DEFAULT 0,
            actionable_item_count INTEGER DEFAULT 0,
            partner_offer_count INTEGER DEFAULT 0,
            
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # 2. Recommendation items table (educational, actionable, partner offers)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendation_items (
            item_id TEXT PRIMARY KEY,
            recommendation_id TEXT NOT NULL,
            item_type TEXT NOT NULL,  -- 'educational', 'actionable', 'partner_offer'
            item_order INTEGER,  -- Display order
            
            -- Educational content (if type='educational')
            content_id TEXT,
            content_title TEXT,
            content_snippet TEXT,
            rationale TEXT,  -- LLM-generated rationale
            
            -- Actionable items (if type='actionable')
            action_text TEXT,
            action_rationale TEXT,
            data_cited TEXT,  -- JSON with cited metrics
            generated_by TEXT,  -- 'llm' or 'template'
            
            -- Partner offers (if type='partner_offer')
            offer_id TEXT,
            offer_title TEXT,
            offer_description TEXT,
            eligibility_passed BOOLEAN,
            eligibility_details TEXT,  -- JSON
            why_relevant TEXT,  -- LLM-generated relevance explanation
            
            FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
        )
    ''')
    
    # 3. Content catalog table (educational content library)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_catalog (
            content_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content_type TEXT,  -- 'article', 'video', 'tool', 'guide'
            snippet TEXT,
            persona_tags TEXT,  -- JSON array
            secondary_tags TEXT,  -- JSON array
            topics TEXT,  -- JSON array
            estimated_read_time_minutes INTEGER,
            difficulty TEXT,  -- 'beginner', 'intermediate', 'advanced'
            content_source TEXT,  -- 'internal', 'external_url'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Partner offers table (product catalog)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partner_offers (
            offer_id TEXT PRIMARY KEY,
            product_type TEXT,
            product_name TEXT,
            short_description TEXT,
            persona_relevance TEXT,  -- JSON array
            eligibility_rules TEXT,  -- JSON
            benefits TEXT,  -- JSON array
            disclaimer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. Generic templates table (pre-approved fallback content)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generic_templates (
            template_id TEXT PRIMARY KEY,
            persona_id INTEGER,
            persona_name TEXT,
            status TEXT DEFAULT 'PRE_APPROVED',
            
            -- Template content stored as JSON
            template_content TEXT,  -- JSON structure matching recommendation package
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for efficient querying
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_recommendations_user 
        ON recommendations(user_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_rec_items_rec_id 
        ON recommendation_items(recommendation_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_rec_items_type 
        ON recommendation_items(item_type)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_content_persona 
        ON content_catalog(persona_tags)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_offers_persona 
        ON partner_offers(persona_relevance)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_templates_persona 
        ON generic_templates(persona_id)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✓ Created recommendation tables in {db_path}")


def insert_recommendation(
    db_path: str,
    recommendation_id: str,
    user_id: str,
    window_30d_persona_id: Optional[int],
    window_180d_persona_id: Optional[int],
    target_personas: List[int],
    educational_items: List[Dict],
    actionable_items: List[Dict],
    partner_offers: List[Dict],
    llm_model: str,
    generation_latency_seconds: float
) -> None:
    """
    Insert a recommendation package into SQLite.
    
    Args:
        db_path: Path to SQLite database
        recommendation_id: Unique recommendation identifier
        user_id: User identifier
        window_30d_persona_id: 30-day window persona ID
        window_180d_persona_id: 180-day window persona ID
        target_personas: List of targeted persona IDs
        educational_items: List of educational content items
        actionable_items: List of actionable items
        partner_offers: List of partner offers
        llm_model: LLM model used for generation
        generation_latency_seconds: Time taken to generate
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Insert parent recommendation record
        cursor.execute('''
            INSERT INTO recommendations (
                recommendation_id, user_id, window_30d_persona_id, window_180d_persona_id,
                target_personas, generated_at, llm_model, generation_latency_seconds,
                educational_item_count, actionable_item_count, partner_offer_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            recommendation_id,
            user_id,
            window_30d_persona_id,
            window_180d_persona_id,
            json.dumps(target_personas),
            datetime.now().isoformat(),
            llm_model,
            generation_latency_seconds,
            len(educational_items),
            len(actionable_items),
            len(partner_offers)
        ))
        
        # Insert educational items
        for idx, item in enumerate(educational_items):
            item_id = f"{recommendation_id}_edu_{idx}"
            cursor.execute('''
                INSERT INTO recommendation_items (
                    item_id, recommendation_id, item_type, item_order,
                    content_id, content_title, content_snippet, rationale
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id,
                recommendation_id,
                'educational',
                idx,
                item.get('content_id'),
                item.get('title'),
                item.get('snippet'),
                item.get('rationale')
            ))
        
        # Insert actionable items
        for idx, item in enumerate(actionable_items):
            item_id = f"{recommendation_id}_act_{idx}"
            cursor.execute('''
                INSERT INTO recommendation_items (
                    item_id, recommendation_id, item_type, item_order,
                    action_text, action_rationale, data_cited, generated_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id,
                recommendation_id,
                'actionable',
                idx,
                item.get('text'),
                item.get('rationale'),
                json.dumps(item.get('data_cited', {})),
                item.get('generated_by', 'llm')
            ))
        
        # Insert partner offers
        for idx, offer in enumerate(partner_offers):
            item_id = f"{recommendation_id}_offer_{idx}"
            cursor.execute('''
                INSERT INTO recommendation_items (
                    item_id, recommendation_id, item_type, item_order,
                    offer_id, offer_title, offer_description,
                    eligibility_passed, eligibility_details, why_relevant
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id,
                recommendation_id,
                'partner_offer',
                idx,
                offer.get('offer_id'),
                offer.get('product_name'),
                offer.get('description'),
                offer.get('eligibility_passed'),
                json.dumps(offer.get('eligibility_details', {})),
                offer.get('why_relevant')
            ))
        
        conn.commit()
        
    except sqlite3.IntegrityError as e:
        print(f"Warning: Recommendation {recommendation_id} already exists, skipping")
        conn.rollback()
    except Exception as e:
        print(f"Error inserting recommendation: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def load_recommendation(db_path: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the most recent recommendation for a user.
    
    Args:
        db_path: Path to SQLite database
        user_id: User identifier
    
    Returns:
        Dictionary containing recommendation data, or None if not found
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Load parent recommendation
        cursor.execute('''
            SELECT * FROM recommendations
            WHERE user_id = ?
            ORDER BY generated_at DESC
            LIMIT 1
        ''', (user_id,))
        
        rec_row = cursor.fetchone()
        if not rec_row:
            return None
        
        recommendation = dict(rec_row)
        recommendation['target_personas'] = json.loads(recommendation['target_personas'])
        
        # Load recommendation items
        cursor.execute('''
            SELECT * FROM recommendation_items
            WHERE recommendation_id = ?
            ORDER BY item_order
        ''', (recommendation['recommendation_id'],))
        
        items = [dict(row) for row in cursor.fetchall()]
        
        # Organize items by type
        recommendation['educational_content'] = []
        recommendation['actionable_items'] = []
        recommendation['partner_offers'] = []
        
        for item in items:
            if item['item_type'] == 'educational':
                recommendation['educational_content'].append({
                    'content_id': item['content_id'],
                    'title': item['content_title'],
                    'snippet': item['content_snippet'],
                    'rationale': item['rationale']
                })
            elif item['item_type'] == 'actionable':
                recommendation['actionable_items'].append({
                    'text': item['action_text'],
                    'rationale': item['action_rationale'],
                    'data_cited': json.loads(item['data_cited']) if item['data_cited'] else {},
                    'generated_by': item['generated_by']
                })
            elif item['item_type'] == 'partner_offer':
                recommendation['partner_offers'].append({
                    'offer_id': item['offer_id'],
                    'product_name': item['offer_title'],
                    'description': item['offer_description'],
                    'eligibility_passed': bool(item['eligibility_passed']),
                    'eligibility_details': json.loads(item['eligibility_details']) if item['eligibility_details'] else {},
                    'why_relevant': item['why_relevant']
                })
        
        return recommendation
        
    finally:
        conn.close()


def load_content_catalog(db_path: str) -> List[Dict[str, Any]]:
    """
    Load all educational content from catalog.
    
    Args:
        db_path: Path to SQLite database
    
    Returns:
        List of content items
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM content_catalog')
    rows = cursor.fetchall()
    
    catalog = []
    for row in rows:
        item = dict(row)
        item['persona_tags'] = json.loads(item['persona_tags']) if item['persona_tags'] else []
        item['secondary_tags'] = json.loads(item['secondary_tags']) if item['secondary_tags'] else []
        item['topics'] = json.loads(item['topics']) if item['topics'] else []
        catalog.append(item)
    
    conn.close()
    return catalog


def load_partner_offers(db_path: str) -> List[Dict[str, Any]]:
    """
    Load all partner offers from catalog.
    
    Args:
        db_path: Path to SQLite database
    
    Returns:
        List of partner offers
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM partner_offers')
    rows = cursor.fetchall()
    
    offers = []
    for row in rows:
        offer = dict(row)
        offer['persona_relevance'] = json.loads(offer['persona_relevance']) if offer['persona_relevance'] else []
        offer['eligibility_rules'] = json.loads(offer['eligibility_rules']) if offer['eligibility_rules'] else {}
        offer['benefits'] = json.loads(offer['benefits']) if offer['benefits'] else []
        offers.append(offer)
    
    conn.close()
    return offers


def load_generic_template(db_path: str, persona_id: int) -> Optional[Dict[str, Any]]:
    """
    Load generic template for a persona.
    
    Args:
        db_path: Path to SQLite database
        persona_id: Persona identifier (1-5, or 0 for stable)
    
    Returns:
        Template dictionary or None
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM generic_templates
        WHERE persona_id = ?
    ''', (persona_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        template = dict(row)
        template['template_content'] = json.loads(template['template_content'])
        return template
    return None


def export_recommendations_to_parquet(db_path: str, output_path: str):
    """
    Export recommendations to Parquet for analytics.
    
    Args:
        db_path: Path to SQLite database
        output_path: Path to output Parquet file
    """
    conn = sqlite3.connect(db_path)
    
    # Load all recommendations
    df = pd.read_sql_query('''
        SELECT 
            user_id,
            recommendation_id,
            generated_at,
            window_30d_persona_id,
            window_180d_persona_id,
            target_personas AS target_personas_json,
            educational_item_count,
            actionable_item_count,
            partner_offer_count,
            generation_latency_seconds,
            llm_model
        FROM recommendations
        ORDER BY generated_at
    ''', conn)
    
    conn.close()
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Parquet
    df.to_parquet(output_path, index=False)
    print(f"✓ Exported {len(df)} recommendations to {output_path}")


def insert_content_catalog_item(db_path: str, content_item: Dict[str, Any]):
    """
    Insert a single content catalog item.
    
    Args:
        db_path: Path to SQLite database
        content_item: Content item dictionary
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO content_catalog (
            content_id, title, content_type, snippet,
            persona_tags, secondary_tags, topics,
            estimated_read_time_minutes, difficulty, content_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        content_item['content_id'],
        content_item['title'],
        content_item['content_type'],
        content_item.get('snippet', ''),
        json.dumps(content_item.get('persona_tags', [])),
        json.dumps(content_item.get('secondary_tags', [])),
        json.dumps(content_item.get('topics', [])),
        content_item.get('estimated_read_time_minutes', 5),
        content_item.get('difficulty', 'beginner'),
        content_item.get('content_source', 'internal')
    ))
    
    conn.commit()
    conn.close()


def insert_partner_offer(db_path: str, offer: Dict[str, Any]):
    """
    Insert a single partner offer.
    
    Args:
        db_path: Path to SQLite database
        offer: Partner offer dictionary
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO partner_offers (
            offer_id, product_type, product_name, short_description,
            persona_relevance, eligibility_rules, benefits, disclaimer
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        offer['offer_id'],
        offer['product_type'],
        offer['product_name'],
        offer['short_description'],
        json.dumps(offer.get('persona_relevance', [])),
        json.dumps(offer.get('eligibility_rules', {})),
        json.dumps(offer.get('benefits', [])),
        offer.get('disclaimer', 'This is educational content, not financial advice.')
    ))
    
    conn.commit()
    conn.close()


def insert_generic_template(db_path: str, template: Dict[str, Any]):
    """
    Insert a generic template.
    
    Args:
        db_path: Path to SQLite database
        template: Template dictionary
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO generic_templates (
            template_id, persona_id, persona_name, status, template_content
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        template['template_id'],
        template['persona_id'],
        template['persona_name'],
        template.get('status', 'PRE_APPROVED'),
        json.dumps(template['template_content'])
    ))
    
    conn.commit()
    conn.close()

