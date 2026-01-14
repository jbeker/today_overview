# Calendar Summary Generator

A tool that consolidates multiple iCal feeds, filters them to today's events, and generates AI-powered summaries of what each person's day looks like.

## Features

- Fetch and parse multiple iCal feeds per person
- Support for shared calendars visible to all
- Filter events to current day
- AI-generated natural language summaries using local LLM
- YAML-based configuration
- Markdown output format

## Prerequisites

Before using this tool, ensure you have the following installed:

### Required Dependencies

1. **yq** - YAML processor
   ```bash
   # macOS (Homebrew)
   brew install yq

   # Linux
   # Download from: https://github.com/mikefarah/yq/releases
   ```

2. **jq** - JSON processor
   ```bash
   # macOS (Homebrew)
   brew install jq

   # Linux
   sudo apt-get install jq  # Debian/Ubuntu
   ```

3. **curl** - HTTP client (usually pre-installed)
   ```bash
   # Verify installation
   curl --version
   ```

4. **Python 3** with required libraries
   ```bash
   # Install Python libraries
   pip3 install icalendar pytz
   ```

5. **llm** - CLI tool for local LLM
   ```bash
   # Install llm tool (if not already installed)
   # Visit: https://llm.datasette.io/
   pip install llm

   # Verify your model is available
   llm -m llama3.1:8b "test"
   ```

## Installation

1. Clone or download this repository:
   ```bash
   cd /path/to/cal_summary
   ```

2. Make the main script executable (should already be done):
   ```bash
   chmod +x cal_summary.sh
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
  # Optional: Override default LLM model
  llm_model: "llama3.1:8b"

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
./cal_summary.sh
```

### Save Output to File

```bash
./cal_summary.sh > daily_summary.md
```

### Automated Daily Summaries

Add to your crontab to run daily:

```bash
# Run at 7 AM every day
0 7 * * * cd /path/to/cal_summary && ./cal_summary.sh > ~/daily_summary_$(date +\%Y\%m\%d).md
```

### Email Daily Summary

Combine with `mail` command:

```bash
./cal_summary.sh | mail -s "Daily Calendar Summary - $(date +\%Y-\%m-\%d)" you@example.com
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

### "Missing required dependencies" error

Install all required dependencies listed in the Prerequisites section.

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
pip3 install icalendar pytz
```

### LLM not found

Ensure the `llm` tool is installed and the model is available:
```bash
llm models list
```

### No events showing up

- Verify the script is filtering for today's date
- Check that events exist on your calendars for today
- Ensure timezone settings are correct

## Customization

### Using a Different LLM Model

Edit `config.yaml`:

```yaml
settings:
  llm_model: "gpt-4"  # or any other model supported by llm CLI
```

### Custom Timezone

Edit `config.yaml`:

```yaml
settings:
  timezone: "America/Los_Angeles"
```

### Modify LLM Prompt

Edit `cal_summary.sh` and customize the `prompt` variable in the main function to change how the LLM generates summaries.

## File Structure

```
cal_summary/
├── cal_summary.sh      # Main bash script
├── parse_ical.py       # Python helper for iCal parsing
├── config.yaml         # Configuration file
└── README.md           # This file
```

## License

This tool is provided as-is for personal use.

## Contributing

Feel free to modify and extend this tool for your needs!
