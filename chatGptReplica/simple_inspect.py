#!/usr/bin/env python3
"""
Simple ChromaDB Inspector - Quick inspection of ChromaDB data
"""

import chromadb
import os
import json
from datetime import datetime

def inspect_chromadb():
    """Simple function to inspect ChromaDB data"""
    # Initialize ChromaDB
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    try:
        client = chromadb.PersistentClient(path=data_dir)
        collections = client.list_collections()
        
        print("🗃️ CHROMADB QUICK INSPECTION")
        print("=" * 50)
        print(f"📁 Data directory: {data_dir}")
        print(f"📊 Collections found: {len(collections)}")
        print()
        
        total_records = 0
        all_records = []
        
        for i, collection in enumerate(collections):
            coll = client.get_collection(collection.name)
            count = coll.count()
            total_records += count
            
            print(f"📄 Collection {i+1}: '{collection.name}'")
            print(f"   📊 Records: {count}")
            
            if count > 0:
                # Get all records for this collection
                results = coll.get(include=['documents', 'metadatas'])
                docs = results.get('documents', [])
                metas = results.get('metadatas', [])
                ids = results.get('ids', [])
                
                # Add to all_records list
                for j, (doc, meta, doc_id) in enumerate(zip(docs, metas, ids)):
                    all_records.append({
                        'record_num': len(all_records) + 1,
                        'collection': collection.name,
                        'id': doc_id,
                        'document': doc,
                        'metadata': meta
                    })
                
                # Show sample
                sample_doc = docs[0][:80] + "..." if len(docs[0]) > 80 else docs[0]
                print(f"   📝 Sample: {sample_doc}")
                
                # Show metadata keys
                if metas and metas[0]:
                    meta_keys = list(metas[0].keys())
                    print(f"   🏷️ Metadata: {meta_keys}")
            print()
        
        print(f"📋 TOTAL RECORDS: {total_records}")
        print("=" * 50)
        
        # Interactive record inspection
        while True:
            print(f"\n👉 Enter record number (1-{len(all_records)}) or 'exit':")
            user_input = input().strip()
            
            if user_input.lower() in ['exit', 'quit']:
                break
                
            try:
                record_num = int(user_input)
                if 1 <= record_num <= len(all_records):
                    record = all_records[record_num - 1]
                    
                    print(f"\n🔍 RECORD {record_num} DETAILS")
                    print("-" * 40)
                    print(f"Collection: {record['collection']}")
                    print(f"ID: {record['id']}")
                    print(f"Content length: {len(record['document'])} chars")
                    print(f"Metadata: {json.dumps(record['metadata'], indent=2)}")
                    print(f"Content:\n{record['document']}")
                    print("-" * 40)
                else:
                    print(f"❌ Please enter a number between 1 and {len(all_records)}")
            except ValueError:
                print("❌ Please enter a valid number or 'exit'")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_chromadb()