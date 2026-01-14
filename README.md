# Calendar Summary Generator

A Python tool that consolidates multiple iCal feeds, filters them to today's events, and generates AI-powered summaries of what each person's day looks like.

## Features

- Fetch and parse multiple iCal feeds per person
- Support for shared calendars visible to all
- Filter events to current day with automatic timezone detection
- AI-generated natural language summaries using Ollama
- YAML-based configuration
- Markdown output format

## Prerequisites

Before using this tool, ensure you have the following installed:

### Required Dependencies

1. **Python 3.8+**
   ```bash
   # Verify installation
   python3 --version
   ```

2. **Python libraries**
   ```bash
   # Install required Python libraries
   pip3 install icalendar pytz requests pyyaml
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
   pip3 install icalendar pytz requests pyyaml
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
python3 cal_summary.py
```

Or if you've made it executable:

```bash
./cal_summary.py
```

### Save Output to File

```bash
python3 cal_summary.py > daily_summary.md
```

### Automated Daily Summaries

Add to your crontab to run daily:

```bash
# Run at 7 AM every day
0 7 * * * cd /path/to/today_overview && python3 cal_summary.py > ~/daily_summary_$(date +\%Y\%m\%d).md
```

### Email Daily Summary

Combine with `mail` command:

```bash
python3 cal_summary.py | mail -s "Daily Calendar Summary - $(date +\%Y-\%m-\%d)" you@example.com
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
pip3 install icalendar pytz requests pyyaml
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
pip3 install icalendar pytz requests pyyaml
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

Edit `cal_summary.py` and customize the prompt in the `generate_summary()` function to change how the AI generates summaries.

## File Structure

```
today_overview/
├── cal_summary.py      # Main Python script
├── parse_ical.py       # Helper for iCal parsing (legacy)
├── config.yaml         # Configuration file
├── .gitignore         # Git ignore rules
└── README.md           # This file
```

## License

This tool is provided as-is for personal use.

## Contributing

Feel free to modify and extend this tool for your needs!
