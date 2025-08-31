#!/usr/bin/env python3
"""
Simple web server to browse and view your processed note cards.
"""

import http.server
import socketserver
import os
import json
import sqlite3
import webbrowser
from pathlib import Path
from urllib.parse import unquote
import argparse

class NotesBrowserHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, processed_dir="notes/processed", db_file="notes.db", **kwargs):
        self.processed_dir = processed_dir
        self.db_file = db_file
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.serve_index()
        elif self.path.startswith("/note/"):
            note_path = unquote(self.path[6:])  # Remove "/note/"
            self.serve_note_card(note_path)
        elif self.path.startswith("/api/notes"):
            self.serve_notes_api()
        else:
            # Serve static files normally
            super().do_GET()
    
    def serve_index(self):
        """Serve the main index page with notes list"""
        html_content = self.generate_index_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_note_card(self, note_path):
        """Serve a specific note card HTML"""
        try:
            full_path = os.path.join(self.processed_dir, note_path, "note_card.html")
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Note card not found")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode('utf-8'))
    
    def serve_notes_api(self):
        """Serve JSON API with notes data"""
        try:
            notes_data = self.get_notes_from_db()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(notes_data).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def get_notes_from_db(self):
        """Get notes from SQLite database"""
        if not os.path.exists(self.db_file):
            return []
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        try:
            c.execute('''
                SELECT id, title, category, tags, summary_short, created_at, 
                       processed_transcript_path, html_card_path
                FROM notes 
                ORDER BY created_at DESC
            ''')
            rows = c.fetchall()
            
            notes = []
            for row in rows:
                note_id, title, category, tags, summary, created_at, md_path, html_path = row
                
                # Extract folder name from path for URL
                if md_path:
                    folder_name = os.path.basename(os.path.dirname(md_path))
                else:
                    folder_name = f"note_{note_id}"
                
                notes.append({
                    "id": note_id,
                    "title": title or "Untitled Note",
                    "category": category or "Uncategorized",
                    "tags": tags.split(", ") if tags else [],
                    "summary": summary or "",
                    "created_at": created_at,
                    "folder_name": folder_name,
                    "has_html_card": html_path and os.path.exists(html_path) if html_path else False
                })
            
            return notes
            
        finally:
            conn.close()
    
    def generate_index_html(self):
        """Generate the main index page"""
        notes = self.get_notes_from_db()
        
        # Get unique categories and tags for filters
        categories = set()
        all_tags = set()
        for note in notes:
            if note["category"]:
                categories.add(note["category"])
            all_tags.update(note["tags"])
        
        categories = sorted(list(categories))
        all_tags = sorted(list(all_tags))
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local Notes Browser</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background-color: #f6f6f6;
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.2rem;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat {{
            background: #f8f8f8;
            padding: 8px 16px;
            border-radius: 8px;
            color: #666;
            font-size: 0.9rem;
            border: 1px solid #eee;
        }}
        
        .filters {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #eee;
        }}
        
        .filter-row {{
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}
        
        .filter-row:last-child {{
            margin-bottom: 0;
        }}
        
        .filter-label {{
            font-weight: 500;
            color: #666;
            min-width: 80px;
        }}
        
        select, input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            color: #333;
            background-color: #f8f8f8;
        }}
        
        select:focus, input:focus {{
            outline: none;
            border-color: #999;
            background-color: white;
        }}
        
        .notes-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .note-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #eee;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }}
        
        .note-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .note-title {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            line-height: 1.3;
        }}
        
        .note-meta {{
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 12px;
            gap: 10px;
        }}
        
        .note-category {{
            background: #f0f0f0;
            color: #666;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid #ddd;
        }}
        
        .note-date {{
            color: #888;
            font-size: 0.85rem;
        }}
        
        .note-summary {{
            color: #666;
            line-height: 1.5;
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            font-size: 0.95rem;
        }}
        
        .note-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .tag {{
            background: #f8f8f8;
            color: #666;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            border: 1px solid #eee;
        }}
        
        .no-notes {{
            text-align: center;
            color: #666;
            font-size: 1.2rem;
            margin-top: 50px;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #eee;
        }}
        
        .view-btn {{
            background: #f8f8f8;
            color: #666;
            border: 1px solid #ddd;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.9rem;
            cursor: pointer;
            margin-top: 10px;
            transition: all 0.2s;
        }}
        
        .view-btn:hover {{
            background: #eee;
            border-color: #ccc;
        }}
        
        .no-card {{
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Local Notes Browser</h1>
            <div class="stats">
                <div class="stat">📄 {len(notes)} Notes</div>
                <div class="stat">📁 {len(categories)} Categories</div>
                <div class="stat">🏷️ {len(all_tags)} Tags</div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-row">
                <span class="filter-label">Search:</span>
                <input type="text" id="searchInput" placeholder="Search titles, summaries, tags..." style="flex: 1; max-width: 300px;">
            </div>
            <div class="filter-row">
                <span class="filter-label">Category:</span>
                <select id="categoryFilter">
                    <option value="">All Categories</option>
                    {"".join([f"<option value='{cat}'>{cat}</option>" for cat in categories])}
                </select>
                <span class="filter-label">Tag:</span>
                <select id="tagFilter">
                    <option value="">All Tags</option>
                    {"".join([f"<option value='{tag}'>{tag}</option>" for tag in all_tags])}
                </select>
            </div>
        </div>
        
        <div class="notes-grid" id="notesGrid">
            {"".join([self.generate_note_card_html(note) for note in notes])}
        </div>
        
        {f'<div class="no-notes" id="noNotesMessage" style="display: none;">No notes found matching your filters.</div>' if notes else '<div class="no-notes">No notes found. Start by adding some audio files to process!</div>'}
    </div>
    
    <script>
        const notes = {json.dumps(notes)};
        let filteredNotes = [...notes];
        
        function renderNotes() {{
            const grid = document.getElementById('notesGrid');
            const noNotesMessage = document.getElementById('noNotesMessage');
            
            if (filteredNotes.length === 0) {{
                grid.innerHTML = '';
                noNotesMessage.style.display = 'block';
            }} else {{
                noNotesMessage.style.display = 'none';
                grid.innerHTML = filteredNotes.map(note => generateNoteCardHTML(note)).join('');
            }}
        }}
        
        function generateNoteCardHTML(note) {{
            const date = new Date(note.created_at).toLocaleDateString();
            const tagsHTML = note.tags.map(tag => `<span class="tag">${{tag}}</span>`).join('');
            const cardClass = note.has_html_card ? '' : 'no-card';
            
            return `
                <div class="note-card ${{cardClass}}" onclick="openNote('${{note.folder_name}}', ${{note.has_html_card}})">
                    <div class="note-title">${{note.title}}</div>
                    <div class="note-meta">
                        <span class="note-category">${{note.category}}</span>
                        <span class="note-date">${{date}}</span>
                    </div>
                    <div class="note-summary">${{note.summary || 'No summary available'}}</div>
                    <div class="note-tags">${{tagsHTML}}</div>
                    <button class="view-btn">${{note.has_html_card ? 'View HTML Card' : 'HTML Card Not Available'}}</button>
                </div>
            `;
        }}
        
        function openNote(folderName, hasHtmlCard) {{
            if (hasHtmlCard) {{
                window.open(`/note/${{folderName}}`, '_blank');
            }} else {{
                alert('HTML card not available for this note. Process it with the enhanced processor first.');
            }}
        }}
        
        function applyFilters() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const categoryFilter = document.getElementById('categoryFilter').value;
            const tagFilter = document.getElementById('tagFilter').value;
            
            filteredNotes = notes.filter(note => {{
                const matchesSearch = !searchTerm || 
                    note.title.toLowerCase().includes(searchTerm) ||
                    note.summary.toLowerCase().includes(searchTerm) ||
                    note.tags.some(tag => tag.toLowerCase().includes(searchTerm));
                
                const matchesCategory = !categoryFilter || note.category === categoryFilter;
                const matchesTag = !tagFilter || note.tags.includes(tagFilter);
                
                return matchesSearch && matchesCategory && matchesTag;
            }});
            
            renderNotes();
        }}
        
        // Event listeners
        document.getElementById('searchInput').addEventListener('input', applyFilters);
        document.getElementById('categoryFilter').addEventListener('change', applyFilters);
        document.getElementById('tagFilter').addEventListener('change', applyFilters);
        
        // Initial render
        renderNotes();
    </script>
</body>
</html>"""
        
        return html
    
    def generate_note_card_html(self, note):
        """Generate HTML for a single note card"""
        date = note['created_at'][:10] if note['created_at'] else 'Unknown'
        tags_html = ''.join([f"<span class='tag'>{tag}</span>" for tag in note['tags']])
        card_class = '' if note['has_html_card'] else 'no-card'
        
        return f"""
            <div class="note-card {card_class}" onclick="openNote('{note['folder_name']}', {str(note['has_html_card']).lower()})">
                <div class="note-title">{note['title']}</div>
                <div class="note-meta">
                    <span class="note-category">{note['category']}</span>
                    <span class="note-date">{date}</span>
                </div>
                <div class="note-summary">{note['summary'] or 'No summary available'}</div>
                <div class="note-tags">{tags_html}</div>
                <button class="view-btn">{'View HTML Card' if note['has_html_card'] else 'HTML Card Not Available'}</button>
            </div>
        """

def main():
    parser = argparse.ArgumentParser(description="Start the notes browser server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--processed-dir", default="notes/processed", help="Directory with processed notes")
    parser.add_argument("--db-file", default="notes.db", help="SQLite database file")
    parser.add_argument("--no-browser", action="store_true", help="Don't automatically open browser")
    
    args = parser.parse_args()
    
    # Create handler with custom parameters
    def handler(*handler_args, **handler_kwargs):
        return NotesBrowserHandler(
            *handler_args, 
            processed_dir=args.processed_dir,
            db_file=args.db_file,
            **handler_kwargs
        )
    
    # Start server
    with socketserver.TCPServer(("", args.port), handler) as httpd:
        print(f"🌐 Notes browser server started at http://localhost:{args.port}")
        print(f"📁 Serving notes from: {args.processed_dir}")
        print(f"🗄️  Using database: {args.db_file}")
        print("Press Ctrl+C to stop the server")
        
        if not args.no_browser:
            webbrowser.open(f"http://localhost:{args.port}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
