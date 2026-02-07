# Calendar Summary Generator

A Python tool that consolidates multiple iCal feeds, filters them to today's events, and generates AI-powered summaries of what each person's day looks like.

## Features

- Fetch and parse multiple iCal feeds per person
- **Recurring event support** — expands RRULE, RDATE, and EXDATE automatically
- Support for shared calendars visible to all
- Filter events to current day with automatic timezone detection
- AI-generated natural language summaries using Ollama
- YAML-based configuration
- Markdown output format

## Prerequisites

Before using this tool, ensure you have the following installed:

### Required Dependencies

1. **Python 3.10+**
   ```bash
   # Verify installation
   python3 --version
   ```

2. **[uv](https://docs.astral.sh/uv/)** (recommended) or pip
   ```bash
   # With uv — no manual install needed, deps are resolved automatically:
   uv run cal_summary.py

   # Or install manually with pip:
   pip3 install icalendar pytz requests pyyaml markdown recurring-ical-events

   # On macOS with Homebrew Python, you may need:
   /opt/homebrew/bin/python3 -m pip install --break-system-packages icalendar pytz requests pyyaml markdown recurring-ical-events
   ```

3. **Ollama** - Local LLM for generating summaries
   ```bash
   # Install Ollama
   # Visit: https://ollama.ai/

   # Pull a model (e.g., llama3.1)
   ollama pull llama3.1:8b

   # Verify Ollama is running
   ollama list
   ```

## Installation

1. Clone this repository:
   ```bash
   git clone git@github.com:jbeker/today_overview.git
   cd today_overview
   ```

2. Install Python dependencies:
   ```bash
   # Recommended: use uv (handles deps automatically via inline metadata)
   uv run cal_summary.py

   # Or install manually:
   pip3 install icalendar pytz requests pyyaml markdown recurring-ical-events

   # For macOS with Homebrew Python (if you get "externally-managed-environment" error)
   /opt/homebrew/bin/python3 -m pip install --break-system-packages icalendar pytz requests pyyaml markdown recurring-ical-events
   ```

3. Configure your calendars in `config.yaml` (see Configuration section below)

## Configuration

Edit `config.yaml` to set up your people and calendar feeds:

```yaml
people:
  - name: Jeremy
    calendars:
      - https://calendar.google.com/calendar/ical/YOUR_CALENDAR_ID/basic.ics
      - https://another-calendar-feed.ics

  - name: Alice
    calendars:
      - https://alice-personal-calendar.ics
      - https://alice-work-calendar.ics

shared_calendars:
  - https://shared-team-calendar.ics
  - https://company-holidays.ics

settings:
  # Optional: Override default Ollama model (defaults to "llama3.1:8b")
  ollama_model: "llama3.1:8b"

  # Optional: Set timezone (defaults to system timezone)
  # timezone: "America/New_York"
```

### Getting iCal Feed URLs

#### Google Calendar
1. Open Google Calendar
2. Click the three dots next to the calendar name
3. Select "Settings and sharing"
4. Scroll to "Integrate calendar"
5. Copy the "Secret address in iCal format" URL

#### iCloud Calendar
1. Open iCloud Calendar on the web
2. Click the share icon next to the calendar
3. Enable "Public Calendar"
4. Copy the webcal:// or https:// URL

#### Other Calendars
Most calendar applications provide an iCal (.ics) feed URL in their sharing or export settings.

## Usage

### Basic Usage

Run the script to generate today's calendar summary:

```bash
# Recommended: uv handles dependencies automatically
uv run cal_summary.py

# Or run directly if deps are installed:
python3 cal_summary.py

# Or if you've made it executable:
./cal_summary.py
```

### Quiet Mode

Suppress INFO messages and only show the LLM summaries:

```bash
python3 cal_summary.py --quiet
# or
python3 cal_summary.py -q
```

This is useful when piping output to files or other commands, as it removes all the progress information and only shows the final summaries.

### JSON Output

Output summaries as a JSON array instead of formatted text:

```bash
python3 cal_summary.py --json
```

The JSON output format includes an array of objects with the following fields:
- `name`: Person's name
- `date`: The date of the summary (ISO format)
- `summary`: The LLM-generated summary text

Example output:
```json
[
  {
    "name": "Jeremy",
    "date": "2026-01-14",
    "summary": "Jeremy has a busy day starting with..."
  },
  {
    "name": "Alice",
    "date": "2026-01-14",
    "summary": "Alice's schedule includes..."
  }
]
```

This is useful for:
- Integration with other tools and scripts
- Programmatic processing of summaries
- Storing summaries in databases
- Building web applications or APIs

**Note:** JSON mode automatically suppresses INFO messages (equivalent to --quiet).

### HTML Output

Convert markdown summaries to HTML format:

```bash
# Output as HTML sections
python3 cal_summary.py --html

# Or combine with JSON for HTML in JSON format
python3 cal_summary.py --json --html
```

**HTML-only mode** (`--html`) outputs HTML fragments with each person's summary wrapped in a `<section>` tag:

```html
<section>
  <h2>Jeremy's Day - 2026-01-14</h2>
  <p>Jeremy has a busy day starting with...</p>
  <!-- More HTML content -->
</section>

<section>
  <h2>Alice's Day - 2026-01-14</h2>
  <p>Alice's schedule includes...</p>
  <!-- More HTML content -->
</section>
```

**Combined JSON+HTML mode** (`--json --html`) outputs JSON with HTML in the summary field:

```json
[
  {
    "name": "Jeremy",
    "date": "2026-01-14",
    "summary": "<p>Jeremy has a busy day starting with...</p>"
  }
]
```

This is useful for:
- Embedding summaries in web pages
- Email newsletters (HTML format)
- CMS integration
- Combining with other HTML content

**Note:** HTML mode automatically suppresses INFO messages and outputs HTML fragments only (no `<html>`, `<head>`, or `<body>` tags).

### Save Output to File

```bash
python3 cal_summary.py --quiet > daily_summary.md

# Save as JSON
python3 cal_summary.py --json > daily_summary.json

# Save as HTML
python3 cal_summary.py --html > daily_summary.html

# Save as JSON with HTML content
python3 cal_summary.py --json --html > daily_summary.json
```

### Automated Daily Summaries

Add to your crontab to run daily:

```bash
# Run at 7 AM every day
0 7 * * * cd /path/to/today_overview && python3 cal_summary.py --quiet > ~/daily_summary_$(date +\%Y\%m\%d).md
```

### Email Daily Summary

Combine with `mail` command:

```bash
python3 cal_summary.py --quiet | mail -s "Daily Calendar Summary - $(date +\%Y-\%m-\%d)" you@example.com
```

## Output Format

The script generates Markdown-formatted output with:

1. Shared calendar events (if any)
2. Individual sections for each person
3. Event details (time, location, description)
4. AI-generated natural language summary

Example output:

```markdown
## Shared Calendar Events

- Team Standup at 09:00
- Company All-Hands at 14:00

## Jeremy

- Morning Workout at 06:30
- Client Meeting at 10:00
- Lunch with Sarah at 12:30

Jeremy has a busy day starting with an early morning workout...
```

## Troubleshooting

### Import or dependency errors

Install all required Python dependencies:
```bash
pip3 install icalendar pytz requests pyyaml markdown recurring-ical-events
```

### "Failed to fetch calendar" warning

- Check that the calendar URL is correct and accessible
- Verify you have an internet connection
- Some calendar feeds may require authentication

### "Failed to parse calendar" warning

- Ensure the URL points to a valid .ics file
- Try downloading the .ics file manually to verify it's valid

### Python import errors

Install required Python libraries:
```bash
pip3 install icalendar pytz requests pyyaml markdown recurring-ical-events
```

### Ollama connection errors

Ensure Ollama is running and the model is available:
```bash
# Check if Ollama is running
ollama list

# If not running, start it (it usually runs as a background service)
# Visit https://ollama.ai/ for installation instructions

# Ensure you have the required model
ollama pull llama3.1:8b
```

### No events showing up

- Verify the script is filtering for today's date
- Check that events exist on your calendars for today
- Ensure timezone settings are correct

## Customization

### Using a Different Ollama Model

Edit `config.yaml`:

```yaml
settings:
  ollama_model: "llama2"  # or any other model available in Ollama
```

Available models can be found with `ollama list` or at https://ollama.ai/library

### Custom Timezone

Edit `config.yaml`:

```yaml
settings:
  timezone: "America/Los_Angeles"
```

### Modify AI Prompt

Edit the `prompt` setting in `config.yaml` to change how the AI generates summaries.

## File Structure

```
today_overview/
├── cal_summary.py              # Main Python script
├── parse_ical.py               # Helper for iCal parsing (legacy)
├── config.yaml                 # Configuration file
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## License

This tool is provided as-is for personal use.

## Contributing

Feel free to modify and extend this tool for your needs!
