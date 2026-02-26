import os
import json
import gzip
import sqlite3
from collections import Counter
from tqdm import tqdm
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from pinecone_text.sparse import BM25Encoder

# ==========================================
# CONFIGURATION & CREDENTIALS
# ==========================================
DB_PATH = "slushpilot_data.db"
GOODREADS_FILE = "C:\\Users\\harel\\Downloads\\goodreads_books.json.gz"
OPENLIBRARY_FILE = "C:\\Users\\harel\\Downloads\\ol_dump_editions_2025-12-31.txt"
MERGED_FILE = "slushpilot_merged_books.jsonl"
PROFILES_FILE = "slushpilot_publisher_profiles.jsonl"
BM25_WEIGHTS_FILE = "bm25_publisher_weights.json"

PINECONE_INDEX_NAME = "slushpilot-publishers"
EMBEDDING_MODEL = "RPRTHPB-text-embedding-3-small"

# Initialize Clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.llmod.ai")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


# ==========================================
# PHASE 1 & 2: STREAMING & DB INGESTION
# ==========================================
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS goodreads (isbn13 TEXT PRIMARY KEY, blurb TEXT, average_rating REAL, ratings_count INTEGER, popular_shelves TEXT)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS openlibrary (isbn13 TEXT PRIMARY KEY, title TEXT, publisher TEXT, genres TEXT)''')
    conn.commit()
    return conn


def process_goodreads(conn):
    """Streams Goodreads. (Uses a line counter because tracking compressed bytes is inaccurate)"""
    cursor = conn.cursor()
    batch = []

    # We use a standard line counter for gzip because uncompressed byte length isn't known upfront
    with gzip.open(GOODREADS_FILE, 'rt', encoding='utf-8') as f:
        for line in tqdm(f, desc="Ingesting Goodreads (Lines)"):
            try:
                book = json.loads(line)
                isbn13 = book.get('isbn13', '').strip()
                if not isbn13: continue

                batch.append((
                    isbn13,
                    book.get('description', ''),
                    float(book.get('average_rating', 0.0)),
                    int(book.get('ratings_count', 0)),
                    json.dumps(book.get('popular_shelves', []))
                ))

                if len(batch) >= 10000:
                    cursor.executemany('INSERT OR IGNORE INTO goodreads VALUES (?, ?, ?, ?, ?)', batch)
                    conn.commit()
                    batch = []
            except Exception:
                pass

    if batch:
        cursor.executemany('INSERT OR IGNORE INTO goodreads VALUES (?, ?, ?, ?, ?)', batch)
        conn.commit()


def process_openlibrary(conn):
    """Streams OpenLibrary using the byte-size tracker."""
    cursor = conn.cursor()
    batch = []
    total_bytes = os.path.getsize(OPENLIBRARY_FILE)

    with tqdm(total=total_bytes, unit='B', unit_scale=True, desc="Ingesting OpenLibrary (Bytes)") as pbar:
        with open(OPENLIBRARY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                pbar.update(len(line.encode('utf-8')))
                cols = line.strip().split('\t')
                if len(cols) >= 5:
                    try:
                        book = json.loads(cols[4])
                        isbn13_list = book.get('isbn_13', [])
                        if not isbn13_list: continue

                        pubs = book.get('publishers', [])
                        if not pubs: continue

                        batch.append((
                            str(isbn13_list[0]).strip(),
                            book.get('title', 'Unknown'),
                            pubs[0],
                            json.dumps(book.get('subjects', []))
                        ))

                        if len(batch) >= 10000:
                            cursor.executemany('INSERT OR IGNORE INTO openlibrary VALUES (?, ?, ?, ?)', batch)
                            conn.commit()
                            batch = []
                    except Exception:
                        pass

    if batch:
        cursor.executemany('INSERT OR IGNORE INTO openlibrary VALUES (?, ?, ?, ?)', batch)
        conn.commit()


# ==========================================
# PHASE 3: SQL JOIN & EXPORT
# ==========================================
def export_joined_data(conn):
    print("Joining datasets in SQLite...")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ol.isbn13, ol.title, ol.publisher, ol.genres, gr.blurb, gr.average_rating, gr.ratings_count, gr.popular_shelves
        FROM openlibrary ol JOIN goodreads gr ON ol.isbn13 = gr.isbn13
    ''')

    with open(MERGED_FILE, 'w', encoding='utf-8') as f:
        for row in tqdm(cursor, desc="Exporting Merged Data"):
            record = {
                "isbn13": row[0], "title": row[1], "publisher": row[2],
                "genres": json.loads(row[3]) if row[3] else [], "blurb": row[4],
                "average_rating": float(row[5]) if row[5] else 0.0,
                "ratings_count": int(row[6]) if row[6] else 0,
                "popular_shelves": json.loads(row[7]) if row[7] else []
            }
            f.write(json.dumps(record) + '\n')


# ==========================================
# PHASE 4: AGGREGATE PROFILES & FIT BM25
# ==========================================
def aggregate_and_fit_bm25():
    publishers = {}
    total_bytes = os.path.getsize(MERGED_FILE)

    # 1. Group by Publisher
    with tqdm(total=total_bytes, unit='B', unit_scale=True, desc="Aggregating Profiles") as pbar:
        with open(MERGED_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                pbar.update(len(line.encode('utf-8')))
                book = json.loads(line)
                pub = book.get('publisher', '').strip()
                if not pub or pub.lower() == 'unknown publisher': continue

                if pub not in publishers:
                    publishers[pub] = {"vol": 0, "total_ratings": 0, "rating_sum": 0.0, "genres": Counter(),
                                       "shelves": Counter(), "books": []}

                p = publishers[pub]
                p["vol"] += 1
                p["genres"].update(book.get('genres', []))
                p["shelves"].update([s['name'] for s in book.get('popular_shelves', [])])

                cnt = book.get('ratings_count', 0)
                p["total_ratings"] += cnt
                p["rating_sum"] += (book.get('average_rating', 0.0) * cnt)
                p["books"].append(
                    {"title": book.get('title', ''), "blurb": book.get('blurb', ''), "ratings_count": cnt})

    # 2. Build Profiles & Prepare Corpus for BM25
    bm25_corpus = []

    with open(PROFILES_FILE, 'w', encoding='utf-8') as out_f:
        for pub_name, data in tqdm(publishers.items(), desc="Finalizing Profiles"):
            if data["vol"] < 2: continue

            avg_rating = round(data["rating_sum"] / data["total_ratings"], 2) if data["total_ratings"] > 0 else 0.0
            sorted_books = sorted(data["books"], key=lambda x: x["ratings_count"], reverse=True)

            comp_titles = [b["title"] for b in sorted_books[:5] if b["title"]]
            top_blurbs = [b["blurb"] for b in sorted_books[:15] if b["blurb"]]
            dense_text = f"Publisher: {pub_name}\n\nTop Books:\n" + "\n---\n".join(top_blurbs)

            top_genres = [g for g, c in data["genres"].most_common(10)]
            top_shelves = [s for s, c in data["shelves"].most_common(10)]
            sparse_keywords = list(set(top_genres + top_shelves))

            # Save to BM25 Corpus to fit the model locally
            bm25_corpus.append(" ".join(sparse_keywords))

            profile = {
                "publisher_id": f"pub_{hash(pub_name) % 100000000}",
                "publisher_name": pub_name,
                "publication_volume": data["vol"],
                "avg_goodreads_rating": avg_rating,
                "recent_comp_titles": comp_titles,
                "active_genres": top_genres,
                "dense_text": dense_text,
                "sparse_text": " ".join(sparse_keywords)  # Pre-joined string for BM25
            }
            out_f.write(json.dumps(profile) + '\n')

    # 3. Fit and Save BM25
    print("Fitting BM25 Encoder to Publisher vocabulary...")
    bm25 = BM25Encoder()
    bm25.fit(bm25_corpus)
    bm25.dump(BM25_WEIGHTS_FILE)
    print(f"BM25 weights saved to {BM25_WEIGHTS_FILE}")


# ==========================================
# PHASE 5: EMBED & UPSERT TO PINECONE
# ==========================================
def embed_and_upsert():
    # 1. Check if the index exists and delete it if it's the wrong one
    if PINECONE_INDEX_NAME in pc.list_indexes().names():
        print(f"Deleting old '{PINECONE_INDEX_NAME}' index...")
        pc.delete_index(PINECONE_INDEX_NAME)

    # 2. Create the new, correct Hybrid Index
    print(f"Creating new '{PINECONE_INDEX_NAME}' index with dotproduct metric...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,  # Required for text-embedding-3-small
        metric="dotproduct",  # ABSOLUTELY REQUIRED for Hybrid Search
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"  # Standard free tier region
        )
    )

    index = pc.Index(PINECONE_INDEX_NAME)
    bm25 = BM25Encoder().load(BM25_WEIGHTS_FILE)

    profiles = []
    with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
        profiles = [json.loads(line) for line in f]

    batch_size = 100  # OpenAI and Pinecone sweet spot

    for i in tqdm(range(0, len(profiles), batch_size), desc="Upserting to Pinecone"):
        batch = profiles[i: i + batch_size]

        # 1. Generate Dense Vectors (Batch Call to OpenAI)
        dense_texts = [p["dense_text"][:8000] for p in batch]  # Truncate just in case to avoid token limits
        res = openai_client.embeddings.create(input=dense_texts, model=EMBEDDING_MODEL)
        dense_vectors = [d.embedding for d in res.data]

        # 2. Generate Sparse Vectors (Local BM25)
        sparse_vectors = bm25.encode_documents([p["sparse_text"] for p in batch])

        # 3. Assemble Pinecone Payloads
        upsert_payload = []
        for idx, p in enumerate(batch):
            metadata = {
                "publisher_name": p["publisher_name"],
                "publication_volume": p["publication_volume"],
                "avg_goodreads_rating": p["avg_goodreads_rating"],
                "recent_comp_titles": p["recent_comp_titles"],
                "active_genres": p["active_genres"]
            }

            # Base record with ID, Dense Vector, and Metadata
            record = {
                "id": p["publisher_id"],
                "values": dense_vectors[idx],
                "metadata": metadata
            }

            # Safely attach the sparse vector ONLY if it contains actual data
            sv = sparse_vectors[idx]
            if sv and len(sv.get("indices", [])) > 0:
                record["sparse_values"] = sv

            upsert_payload.append(record)

        # 4. Push to Pinecone
        index.upsert(vectors=upsert_payload)

    print("All publisher vectors successfully upserted to Pinecone!")


# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    # Feel free to comment out phases you have already run!

    # conn = setup_database()
    # process_goodreads(conn)
    # process_openlibrary(conn)
    # export_joined_data(conn)
    # conn.close()

    # aggregate_and_fit_bm25()

    embed_and_upsert()
