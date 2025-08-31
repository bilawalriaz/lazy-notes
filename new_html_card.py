import os
import json
from datetime import datetime

def create_html_card(structured_data, original_transcript, output_path):
    """Create a modern HTML card based on the newcard React component."""
    
    # Extract data with safe defaults
    title = structured_data.get("title", "Untitled Note")
    cleaned_transcript = structured_data.get("cleaned_transcript", original_transcript)
    category = structured_data.get("category", "Uncategorized")
    tags = structured_data.get("tags", [])
    summary = structured_data.get("summary_short", "")
    key_points = structured_data.get("key_points", [])
    action_items = structured_data.get("action_items", [])
    decisions = structured_data.get("decisions", [])
    questions = structured_data.get("questions", [])
    people = structured_data.get("people", [])
    entities = structured_data.get("entities", [])
    time_extractions = structured_data.get("time_extractions", [])

    # Helper functions
    def get_priority_classes(priority):
        return {
            "H": "bg-red-100 text-red-800 border-red-200",
            "M": "bg-yellow-100 text-yellow-800 border-yellow-200",
            "L": "bg-green-100 text-green-800 border-green-200"
        }.get(priority, "bg-gray-100 text-gray-800 border-gray-200")

    def get_priority_text(priority):
        return {"H": "High", "M": "Medium", "L": "Low"}.get(priority, "Low")

    def format_date(date_string):
        if not date_string:
            return ""
        try:
            # Assuming date is in ISO format (e.g., "2024-06-11")
            dt = datetime.fromisoformat(date_string)
            return dt.strftime("%b %d, %Y")
        except (ValueError, TypeError):
            return date_string

    def create_section(title, icon, content, condition=True):
        if not condition:
            return ""
        return f'''
        <div class="space-y-4">
            <h3 class="font-bold text-gray-900 flex items-center gap-2 text-lg">
                <span data-lucide="{icon}" class="w-5 h-5 text-blue-600"></span>
                {title}
            </h3>
            {content}
        </div>
        '''

    # --- Build HTML sections ---

    tags_html = ""
    if tags:
        tags_html = '<div class="flex flex-wrap gap-2">' + "".join([
            f'<span class="badge bg-indigo-50 text-indigo-700 border-indigo-200 font-medium px-3 py-1">#{tag}</span>' 
            for tag in tags
        ]) + '</div>'

    key_points_html = ""
    if key_points:
        key_points_html = '<ul class="space-y-3">' + "".join([
            f'''<li class="flex items-start gap-3 text-gray-700 font-medium">
                <div class="w-2 h-2 bg-blue-600 rounded-full mt-2.5 flex-shrink-0"></div>
                {point}
            </li>'''
            for point in key_points
        ]) + '</ul>'

    action_items_html = ""
    if action_items:
        action_items_html = '<div class="space-y-3">' + "".join([
            f'''<div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
                <div class="flex-1">
                    <span class="text-gray-800 font-medium">{item.get("description", "")}</span>
                    {'''
                    <div class="flex items-center gap-1.5 mt-1 text-sm text-gray-600">
                        <span data-lucide="calendar" class="w-3.5 h-3.5"></span>
                        Due: {format_date(item.get("due"))}
                    </div>
                    ''' if item.get("due") else ""}
                </div>
                <span class="badge {get_priority_classes(item.get("priority", "L"))} font-semibold ml-4">
                    {get_priority_text(item.get("priority", "L"))}
                </span>
            </div>'''
            for item in action_items
        ]) + '</div>'

    decisions_html = ""
    if decisions:
        decisions_html = '<ul class="space-y-3">' + "".join([
            f'''<li class="flex items-start gap-3 text-gray-700 font-medium">
                <div class="w-2 h-2 bg-green-600 rounded-full mt-2.5 flex-shrink-0"></div>
                {decision}
            </li>'''
            for decision in decisions
        ]) + '</ul>'

    questions_html = ""
    if questions:
        questions_html = '<ul class="space-y-3">' + "".join([
            f'''<li class="flex items-start gap-3 text-gray-700 font-medium">
                <div class="w-2 h-2 bg-orange-500 rounded-full mt-2.5 flex-shrink-0"></div>
                {question}
            </li>'''
            for question in questions
        ]) + '</ul>'

    people_html = ""
    if people:
        people_html = '<div class="flex flex-wrap gap-2">' + "".join([
            f'<span class="badge bg-purple-50 text-purple-700 border-purple-200 font-medium px-3 py-1">{person}</span>'
            for person in people
        ]) + '</div>'

    entities_html = ""
    if entities:
        entities_html = '<div class="flex flex-wrap gap-2">' + "".join([
            f'''<span class="badge bg-teal-50 text-teal-700 border-teal-200 font-medium px-3 py-1">
                {entity.get("text", "")} <span class="text-teal-500 text-xs ml-1">({entity.get("type", "")})</span>
            </span>'''
            for entity in entities
        ]) + '</div>'

    time_extractions_html = ""
    if time_extractions:
        time_extractions_html = '<div class="flex flex-wrap gap-2">' + "".join([
            f'''<span class="badge bg-amber-50 text-amber-700 border-amber-200 font-medium px-3 py-1">
                {time.get("text", "")} → {time.get("normalized", "")} <span class="text-amber-500 text-xs ml-1">({time.get("kind", "")})</span>
            </span>'''
            for time in time_extractions
        ]) + '</div>'

    # Safely escape transcripts for JavaScript
    js_original_transcript = json.dumps(original_transcript) if original_transcript else '""'
    js_cleaned_transcript = json.dumps(cleaned_transcript)

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Work Sans', sans-serif;
            background-color: #f8fafc; /* A neutral background */
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            border-radius: 9999px;
            border-width: 1px;
            font-size: 0.875rem;
            line-height: 1.25rem;
        }}
    </style>
</head>
<body class="bg-background p-4">
    <main class="max-w-6xl mx-auto space-y-8">
        <div class="w-full max-w-4xl mx-auto shadow-lg bg-white border border-gray-200 rounded-lg">
            <div class="bg-white border-b border-gray-100 p-4 rounded-t-lg">
                <div class="flex items-start justify-between gap-4">
                    <div class="flex-1">
                        <h1 class="text-2xl font-bold text-gray-900 text-balance font-sans leading-tight">{title}</h1>
                        <div class="flex items-center gap-3 mt-3">
                            <span class="badge bg-blue-50 text-blue-700 border-blue-200 font-medium px-3 py-1">{category}</span>
                            <span class="text-sm text-gray-500 flex items-center gap-1.5 font-medium">
                                <span data-lucide="clock" class="w-4 h-4"></span>
                                Just now
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="p-4 space-y-6 bg-white rounded-b-lg">
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 id="transcript-title" class="font-bold text-gray-900 text-lg">Cleaned Transcript</h3>
                        {"<button id='toggle-button' class='flex items-center gap-2 border-gray-200 hover:bg-gray-50 rounded-md px-3 py-1 text-sm font-semibold' onclick='toggleTranscript()'><span data-lucide='toggle-left' class='w-4 h-4'></span><span id='toggle-text'>Show Original</span></button>" if original_transcript else ""}
                    </div>
                    <div class="bg-gray-50 p-5 rounded-xl border border-gray-100">
                        <p id="transcript-text" class="text-gray-800 leading-relaxed whitespace-pre-wrap font-medium">{cleaned_transcript}</p>
                    </div>
                </div>

                <div class="bg-gray-200" style="height: 1px;"></div>

                {create_section("Summary", "file-text", f'<p class="text-gray-700 leading-relaxed bg-gray-50 p-5 rounded-xl font-medium">{summary}</p>', summary)}
                {create_section("Tags", "hash", tags_html, tags)}
                {create_section("Key Points", "target", key_points_html, key_points)}
                {create_section("Action Items", "check-circle", action_items_html, action_items)}
                {create_section("Decisions", "check-circle", decisions_html, decisions)}
                {create_section("Questions", "help-circle", questions_html, questions)}
                {create_section("People Mentioned", "users", people_html, people)}
                {create_section("Entities", "building-2", entities_html, entities)}
                {create_section("Time References", "clock", time_extractions_html, time_extractions)}

               <!-- <div class="flex gap-3 pt-4">
                    <button class="bg-blue-600 text-white hover:bg-blue-700 font-semibold px-4 py-2 rounded-md text-sm">Edit</button>
                    <button class="border border-gray-200 hover:bg-gray-50 font-semibold bg-transparent px-4 py-2 rounded-md text-sm">Share</button>
                    <button class="border border-gray-200 hover:bg-gray-50 font-semibold bg-transparent px-4 py-2 rounded-md text-sm">Export</button>
                </div> -->
            </div>
        </div>
    </main>

    <script>
        lucide.createIcons();

        const originalTranscript = {js_original_transcript};
        const cleanedTranscript = {js_cleaned_transcript};
        let showingOriginal = false;

        function toggleTranscript() {{
            const titleEl = document.getElementById('transcript-title');
            const textEl = document.getElementById('transcript-text');
            const toggleTextEl = document.getElementById('toggle-text');
            const toggleButtonEl = document.getElementById('toggle-button');
            
            showingOriginal = !showingOriginal;

            if (showingOriginal) {{
                titleEl.innerText = 'Original Transcript';
                textEl.innerText = originalTranscript;
                toggleTextEl.innerText = 'Show Cleaned';
                toggleButtonEl.querySelector('span[data-lucide]').setAttribute('data-lucide', 'toggle-right');
            }} else {{
                titleEl.innerText = 'Cleaned Transcript';
                textEl.innerText = cleanedTranscript;
                toggleTextEl.innerText = 'Show Original';
                toggleButtonEl.querySelector('span[data-lucide]').setAttribute('data-lucide', 'toggle-left');
            }}
            lucide.createIcons(); // Re-render icons
        }}
    </script>
</body>
</html>'''

    html_path = os.path.join(output_path, "note_card.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return html_path