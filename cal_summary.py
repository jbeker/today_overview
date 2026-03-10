#!/opt/homebrew/bin/python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "icalendar",
#     "pytz",
#     "requests",
#     "pyyaml",
#     "markdown",
#     "recurring-ical-events",
# ]
# ///
"""
Calendar Summary Generator
Fetches iCal feeds, filters today's events, and generates AI summaries using Ollama.
"""

import sys
import os
import json
import re
import argparse
import requests
from datetime import datetime, date, timedelta
from icalendar import Calendar
import pytz
import recurring_ical_events
import yaml
import markdown
import subprocess
import tempfile
import shutil
from io import StringIO


# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.yaml")

# Global quiet flag
QUIET = False


def log_info(message):
    """Print info message to stderr."""
    if not QUIET:
        print(f"\033[0;32m[INFO]\033[0m {message}", file=sys.stderr)


def log_warn(message):
    """Print warning message to stderr."""
    print(f"\033[1;33m[WARN]\033[0m {message}", file=sys.stderr)


def log_error(message):
    """Print error message to stderr."""
    print(f"\033[0;31m[ERROR]\033[0m {message}", file=sys.stderr)


def markdown_to_html(text):
    """Convert markdown text to HTML."""
    return markdown.markdown(text, extensions=['extra', 'nl2br'])


def get_local_timezone():
    """Get the system's local timezone as a pytz timezone."""
    # Try to get timezone from environment variable
    tz_name = os.environ.get('TZ')

    if not tz_name:
        # Read the /etc/localtime symlink (works on macOS and Linux regardless of DST)
        try:
            link_target = os.path.realpath('/etc/localtime')
            marker = '/zoneinfo/'
            idx = link_target.find(marker)
            if idx != -1:
                tz_name = link_target[idx + len(marker):]
        except OSError:
            pass

    if not tz_name:
        # FreeBSD copies the zoneinfo file instead of symlinking; the name is in /var/db/zoneinfo
        try:
            with open('/var/db/zoneinfo', 'r') as f:
                tz_name = f.read().strip()
        except OSError:
            pass

    if not tz_name:
        tz_name = 'UTC'

    try:
        return pytz.timezone(tz_name)
    except:
        return pytz.UTC


def get_event_datetime(dt, local_tz):
    """Convert an iCal datetime to a timezone-aware datetime object in local timezone."""
    if dt is None:
        return None

    # If it's a date object (all-day event), convert to datetime
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return datetime.combine(dt, datetime.min.time())

    # If it's already a datetime
    if isinstance(dt, datetime):
        # If it's naive (no timezone), assume UTC and convert to local
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)

        # Convert to local timezone
        if local_tz:
            dt = dt.astimezone(local_tz)

        return dt

    return dt


def parse_ical(ics_content, target_date=None, local_tz=None):
    """
    Parse iCal content and extract events for the target date.

    Args:
        ics_content: String containing .ics file content
        target_date: datetime.date object (defaults to today)
        local_tz: pytz timezone (defaults to system timezone)

    Returns:
        List of event dictionaries
    """
    if target_date is None:
        target_date = date.today()

    if local_tz is None:
        local_tz = get_local_timezone()

    # Parse calendar
    try:
        cal = Calendar.from_ical(ics_content)
    except Exception as e:
        log_error(f"Error parsing iCal: {e}")
        return []

    events = []

    # Expand recurring events (RRULE, RDATE) and apply EXDATE exclusions
    try:
        recurring_events = recurring_ical_events.of(cal, skip_bad_series=True).at(target_date)
    except Exception as e:
        log_warn(f"Error expanding recurring events: {e}")
        recurring_events = []

    for component in recurring_events:
        try:
            summary = str(component.get('summary', 'No Title'))
            description = str(component.get('description', ''))
            location = str(component.get('location', ''))

            dtstart = component.get('dtstart')
            dtend = component.get('dtend')

            if dtstart is None:
                continue

            start_dt = get_event_datetime(dtstart.dt, local_tz)
            end_dt = get_event_datetime(dtend.dt if dtend else None, local_tz)

            is_all_day = isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime)

            event_data = {
                'summary': summary,
                'description': description,
                'location': location,
                'start': start_dt.isoformat() if isinstance(start_dt, datetime) else str(start_dt),
                'end': end_dt.isoformat() if isinstance(end_dt, datetime) else str(end_dt) if end_dt else None,
                'all_day': is_all_day
            }

            events.append(event_data)

        except Exception as e:
            log_warn(f"Error processing event: {e}")
            continue

    # Sort events by start time
    events.sort(key=lambda x: x['start'])

    return events


def fetch_and_parse_calendar(url, local_tz, target_date=None):
    """Fetch and parse a calendar from a URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        ics_content = response.text
        return parse_ical(ics_content, target_date=target_date, local_tz=local_tz)
    except requests.RequestException as e:
        log_warn(f"Failed to fetch calendar: {url[:50]}... - {e}")
        return []
    except Exception as e:
        log_warn(f"Failed to parse calendar: {url[:50]}... - {e}")
        return []


def filter_events(events, ignore_patterns):
    """Filter out events whose summary matches any of the given regex patterns.

    Args:
        events: List of event dictionaries (each must have a 'summary' key)
        ignore_patterns: List of regex pattern strings to match against summaries

    Returns:
        Filtered list of events
    """
    if not ignore_patterns:
        return events
    compiled = [re.compile(p, re.IGNORECASE) for p in ignore_patterns]
    return [e for e in events if not any(r.search(e['summary']) for r in compiled)]


def format_event_time(event):
    """Format event time for display."""
    if event['all_day']:
        return "all day"

    start = event['start']
    end = event['end']

    if end:
        # Extract time portion (HH:MM:SS) from ISO format
        start_time = start.split('T')[1].split('-')[0].split('+')[0] if 'T' in start else start
        end_time = end.split('T')[1].split('-')[0].split('+')[0] if 'T' in end else end
        return f"{start_time} to {end_time}"
    else:
        start_time = start.split('T')[1].split('-')[0].split('+')[0] if 'T' in start else start
        return start_time


def clean_description(description):
    """Clean up event description by removing call-in details."""
    if not description:
        return description

    # List of markers that indicate call-in information starts
    truncate_markers = [
        "Join Zoom Meeting",
        "Microsoft Teams Need help",
        "________________________________________________________________________________",
        "Join the meeting now",
        "Dial in by phone",
        "Join Meeting",
        "Meeting ID:",
        "Passcode:"
    ]

    # Find the earliest occurrence of any marker
    earliest_pos = len(description)
    for marker in truncate_markers:
        pos = description.find(marker)
        if pos != -1 and pos < earliest_pos:
            earliest_pos = pos

    # Truncate at the marker
    if earliest_pos < len(description):
        description = description[:earliest_pos].strip()

    return description


def format_event(event):
    """Format a single event as markdown."""
    lines = [f"- **{event['summary']}**: {format_event_time(event)}"]

    if event['location']:
        lines.append(f"  Location: {event['location']}")

    if event['description']:
        cleaned_desc = clean_description(event['description'])
        if cleaned_desc:
            lines.append(f"  Description: {cleaned_desc}")

    return '\n'.join(lines)


def build_person_events_data(person_name, person_calendars, shared_calendars):
    """Build the events data section for a single person's LLM prompt."""
    lines = []

    # Add person's calendars
    lines.append(f"## {person_name}'s Schedule\n")

    if not person_calendars:
        lines.append("No personal calendars configured.\n")
    else:
        for calendar in person_calendars:
            description = calendar['description']
            events = calendar['events']

            if events:
                lines.append(f"### {description}\n")
                for event in events:
                    lines.append(format_event(event))
                    lines.append("")
                lines.append("")

    # Add shared calendars
    if shared_calendars:
        lines.append("## Shared/Family Events\n")

        for calendar in shared_calendars:
            description = calendar['description']
            events = calendar['events']

            if events:
                lines.append(f"### {description}\n")
                for event in events:
                    lines.append(format_event(event))
                    lines.append("")
                lines.append("")

    return '\n'.join(lines)


def call_ollama(prompt, model, ollama_url):
    """Call Ollama API to generate summary.

    Raises:
        RuntimeError: If the API call fails or returns empty response
    """
    api_url = f"{ollama_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(api_url, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        llm_response = result.get('response', '')

        if not llm_response or not llm_response.strip():
            raise RuntimeError("LLM returned empty response")

        return llm_response
    except requests.RequestException as e:
        log_error(f"Failed to call Ollama API: {e}")
        raise RuntimeError(f"Ollama API call failed: {e}")
    except Exception as e:
        log_error(f"Error processing Ollama response: {e}")
        raise RuntimeError(f"Error processing Ollama response: {e}")


def call_llm_command(prompt, command):
    """Call an external LLM CLI tool by piping the prompt to it via stdin.

    Args:
        prompt: The prompt text to send
        command: The shell command to run (e.g. "claude -p")

    Raises:
        RuntimeError: If the command fails or returns empty output
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode != 0:
            stderr_msg = result.stderr.strip() if result.stderr else "unknown error"
            raise RuntimeError(f"LLM command failed (exit {result.returncode}): {stderr_msg}")

        output = result.stdout
        if not output or not output.strip():
            raise RuntimeError("LLM command returned empty output")

        return output
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"LLM command timed out after 600 seconds")
    except FileNotFoundError:
        raise RuntimeError(f"LLM command not found: {command}")


def main(debug=False, quiet=False, output_format='text', use_html=False, output_file=None,
         target_date=None, date_label=None, full_date_str=None, user=None):
    """Main entry point.

    Args:
        debug: If True, show prompts without calling LLM
        quiet: If True, suppress INFO messages
        output_format: Output format ('text', 'json', or 'html')
        use_html: If True, convert markdown to HTML
        output_file: Optional file path to write output to. If specified and an error
                     occurs or LLM returns no response, existing file won't be overwritten.
        target_date: Date to fetch events for (defaults to today)
        date_label: Human label like "today", "tomorrow", or "Thursday, February 20"
        full_date_str: Full date string like "Saturday, February 14, 2026"
    """
    global QUIET
    QUIET = quiet

    # In JSON or HTML mode, always suppress INFO messages
    if output_format == 'json' or output_format == 'html':
        QUIET = True

    # Set up output capturing if writing to file
    original_stdout = sys.stdout
    output_buffer = None
    success = False
    if output_file:
        output_buffer = StringIO()
        sys.stdout = output_buffer

    try:
        if debug:
            log_info("Starting calendar summary generator (DEBUG MODE - no LLM calls)...")
        else:
            log_info("Starting calendar summary generator...")

        # Load config
        if not os.path.exists(CONFIG_FILE):
            log_error(f"Config file not found: {CONFIG_FILE}")
            raise RuntimeError(f"Config file not found: {CONFIG_FILE}")

        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)

        # Get settings
        settings = config.get('settings', {})
        llm_model = settings.get('llm_model', 'llama3.1:8b')
        ollama_url = settings.get('ollama_url', 'https://ollama.confusticate.com')
        llm_command = settings.get('llm_command')
        prompt_template = settings.get('llm_prompt')

        # Get timezone (config override > system detection)
        config_tz = settings.get('timezone')
        if config_tz:
            try:
                local_tz = pytz.timezone(config_tz)
            except pytz.exceptions.UnknownTimeZoneError:
                log_warn(f"Unknown timezone '{config_tz}' in config, falling back to system detection")
                local_tz = get_local_timezone()
        else:
            local_tz = get_local_timezone()

        # Process each person's calendars
        log_info("Fetching personal calendars...")
        person_calendars = {}

        people = config.get('people', [])
        if user:
            people = [p for p in people if p['name'].lower() == user.lower()]
            if not people:
                available = [p['name'] for p in config.get('people', [])]
                log_error(f"User '{user}' not found in config. Available: {', '.join(available)}")
                raise RuntimeError(f"User '{user}' not found")

        for person in people:
            person_name = person['name']
            log_info(f"Processing calendars for: {person_name}")

            calendars = []
            for calendar_config in person.get('calendars', []):
                url = calendar_config['url']
                description = calendar_config.get('description', '')

                log_info(f"  Fetching: {url[:50]}...")
                if description:
                    log_info(f"    Description: {description}")

                events = fetch_and_parse_calendar(url, local_tz, target_date=target_date)
                ignore_patterns = calendar_config.get('ignore_patterns', [])
                events = filter_events(events, ignore_patterns)

                calendars.append({
                    'description': description,
                    'events': events
                })

            person_calendars[person_name] = calendars

        # Process shared calendars
        log_info("Fetching shared calendars...")
        shared_calendars = []

        for calendar_config in config.get('shared_calendars', []):
            url = calendar_config['url']
            description = calendar_config.get('description', '')

            log_info(f"  Fetching: {url[:50]}...")
            if description:
                log_info(f"    Description: {description}")

            events = fetch_and_parse_calendar(url, local_tz, target_date=target_date)
            ignore_patterns = calendar_config.get('ignore_patterns', [])
            events = filter_events(events, ignore_patterns)

            shared_calendars.append({
                'description': description,
                'events': events
            })

        # Generate individual summaries for each person
        log_info("Generating individual summaries...")
        if target_date is None:
            target_date = date.today()
        if date_label is None:
            date_label = "today"
        if full_date_str is None:
            full_date_str = target_date.strftime("%A, %B %-d, %Y")
        target_date_str = target_date.isoformat()

        # Compute header label
        if date_label == "today":
            header_label = "Day"
        elif date_label == "tomorrow":
            header_label = "Tomorrow"
        else:
            header_label = f"Schedule ({date_label})"

        # Use custom prompt template or default
        if not prompt_template:
            prompt_template = (
                "You are a helpful assistant that summarizes calendar events. "
                "Below are {date_label}'s events ({full_date}) for {person_name}. "
                "Please provide a concise, friendly summary of what their day looks like. "
                "Format your response in Markdown.\n\n"
                "{events_data}\n\n"
                "Please provide a natural language summary of {person_name}'s day, "
                "highlighting key events and the overall schedule."
            )

        # Collect summaries for JSON output
        summaries = []

        # Process each person
        for person_name, calendars in person_calendars.items():
            log_info(f"Generating summary for {person_name}...")

            # Build events data for this person
            events_data = build_person_events_data(person_name, calendars, shared_calendars)

            # Build prompt
            prompt = (prompt_template
                      .replace('{today}', target_date_str)
                      .replace('{target_date}', target_date_str)
                      .replace('{full_date}', full_date_str)
                      .replace('{date_label}', date_label)
                      .replace('{person_name}', person_name)
                      .replace('{events_data}', events_data))

            if debug:
                # Debug mode: print prompt instead of calling LLM
                print(f"\n{'='*60}")
                print(f"  DEBUG: Prompt for {person_name}")
                print(f"{'='*60}\n")
                print(prompt)
                print(f"\n{'='*60}")
                print(f"  End of prompt for {person_name}")
                print(f"{'='*60}\n")
            else:
                # Call LLM (via command or Ollama API)
                if llm_command:
                    log_info(f"  Calling LLM command: {llm_command}")
                    response = call_llm_command(prompt, llm_command)
                else:
                    log_info(f"  Calling Ollama (model: {llm_model})...")
                    response = call_ollama(prompt, llm_model, ollama_url)

                # Convert to HTML if requested
                if use_html:
                    response = markdown_to_html(response)

                if output_format in ['json', 'html']:
                    # Collect summary for JSON or HTML output
                    summaries.append({
                        'name': person_name,
                        'date': target_date_str,
                        'summary': response
                    })
                else:
                    # Print response with header (text format)
                    print(f"\n{'='*60}")
                    print(f"  {person_name}'s {header_label} - {target_date_str}")
                    print(f"{'='*60}\n")
                    print(response)
                    print()

        # Output results based on format
        if output_format == 'json':
            print(json.dumps(summaries, indent=2))
        elif output_format == 'html':
            # Output HTML sections
            for summary in summaries:
                print(f'<section>')
                print(f'  <h2>{summary["name"]}\'s {header_label} - {summary["date"]}</h2>')
                print(f'  {summary["summary"]}')
                print(f'</section>')
                print()

        if debug:
            log_info("Debug mode complete - no LLM calls were made.")
        else:
            log_info("All summaries generated!")

        # Mark success so we write to file in finally block
        success = True

    except RuntimeError as e:
        # Error occurred - restore stdout and don't write to file
        sys.stdout = original_stdout
        log_error(f"Failed to generate summaries: {e}")
        if output_file:
            log_error(f"Output file '{output_file}' was not modified due to error")
        sys.exit(1)
    except Exception as e:
        # Unexpected error - restore stdout and don't write to file
        sys.stdout = original_stdout
        log_error(f"Unexpected error: {e}")
        if output_file:
            log_error(f"Output file '{output_file}' was not modified due to error")
        sys.exit(1)
    finally:
        # Restore stdout
        sys.stdout = original_stdout

        # Write to file only if we succeeded and output_file was specified
        if success and output_file and output_buffer:
            output_content = output_buffer.getvalue()

            # Only write if we have content
            if output_content.strip():
                try:
                    # Write to temporary file first
                    temp_fd, temp_path = tempfile.mkstemp(
                        dir=os.path.dirname(os.path.abspath(output_file)),
                        prefix='.tmp_',
                        suffix='_summary'
                    )

                    with os.fdopen(temp_fd, 'w') as temp_file:
                        temp_file.write(output_content)

                    # Atomically replace the output file
                    shutil.move(temp_path, output_file)
                    log_info(f"Output written to: {output_file}")
                except Exception as e:
                    log_error(f"Failed to write output file: {e}")
                    # Clean up temp file if it exists
                    if 'temp_path' in locals() and os.path.exists(temp_path):
                        os.unlink(temp_path)
                    sys.exit(1)
            else:
                log_error("No output generated - output file not modified")
                sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate calendar summaries using Ollama LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Normal mode: fetch calendars and generate summaries
  %(prog)s --debug                # Debug mode: show prompts without calling LLM
  %(prog)s --quiet                # Quiet mode: suppress INFO messages, only show summaries
  %(prog)s -q                     # Same as --quiet
  %(prog)s --json                 # Output summaries as JSON array (markdown format)
  %(prog)s --html                 # Output summaries as HTML sections
  %(prog)s --json --html          # Output summaries as JSON array (HTML format)
  %(prog)s -o summary.txt         # Write output to summary.txt (safe from errors)
  %(prog)s --json -o summary.json # Write JSON output to summary.json
  %(prog)s --tomorrow             # Fetch events for tomorrow
  %(prog)s --date 2026-02-20      # Fetch events for a specific date
        """
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug mode: show prompts without calling LLM'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode: suppress INFO messages, only show summaries and errors'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output summaries as JSON array with name, date, and summary fields'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Convert summaries from markdown to HTML (can be combined with --json)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        metavar='FILE',
        help='Write output to FILE. If an error occurs or LLM returns no response, existing file will not be overwritten'
    )

    parser.add_argument(
        '-u', '--user',
        type=str,
        metavar='NAME',
        help='Generate summary for a single user only (must match a name in config.yaml)'
    )

    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        '--tomorrow',
        action='store_true',
        help="Fetch events for tomorrow instead of today"
    )
    date_group.add_argument(
        '--date',
        type=str,
        metavar='YYYY-MM-DD',
        help='Fetch events for a specific date (ISO format: YYYY-MM-DD)'
    )

    args = parser.parse_args()

    # Compute target date
    if args.tomorrow:
        target_date = date.today() + timedelta(days=1)
        date_label = "tomorrow"
    elif args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            parser.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
        if target_date == date.today():
            date_label = "today"
        elif target_date == date.today() + timedelta(days=1):
            date_label = "tomorrow"
        else:
            date_label = target_date.strftime("%A, %B %-d")
    else:
        target_date = date.today()
        date_label = "today"

    full_date_str = target_date.strftime("%A, %B %-d, %Y")

    # Determine output format and HTML conversion
    if args.json:
        output_format = 'json'
    elif args.html:
        output_format = 'html'
    else:
        output_format = 'text'

    use_html = args.html

    main(debug=args.debug, quiet=args.quiet, output_format=output_format, use_html=use_html,
         output_file=args.output, target_date=target_date, date_label=date_label,
         full_date_str=full_date_str, user=args.user)
