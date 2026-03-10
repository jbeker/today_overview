#!/usr/bin/env python3
"""
Parse iCal (.ics) files and extract today's events.
Reads .ics content from stdin and outputs JSON to stdout.
"""

import sys
import json
import os
from datetime import datetime, date, timedelta
from icalendar import Calendar
import pytz


def get_local_timezone():
    """Get the system's local timezone as a pytz timezone."""
    # Try to get timezone from environment variable
    tz_name = os.environ.get('TZ')

    if not tz_name:
        # Read the /etc/localtime symlink (works on macOS and Linux regardless of DST)
        try:
            link_target = os.path.realpath('/etc/localtime')
            # Extract IANA timezone name from path (e.g. .../zoneinfo/America/New_York)
            marker = '/zoneinfo/'
            idx = link_target.find(marker)
            if idx != -1:
                tz_name = link_target[idx + len(marker):]
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
        # If it's naive (no timezone), assume it's in UTC and convert to local
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)

        # Convert to local timezone
        if local_tz:
            dt = dt.astimezone(local_tz)

        return dt

    return dt


def parse_ical(ics_content, target_date=None, timezone_name=None):
    """
    Parse iCal content and extract events for the target date.

    Args:
        ics_content: String containing .ics file content
        target_date: datetime.date object (defaults to today)
        timezone_name: IANA timezone name (defaults to system timezone)

    Returns:
        List of event dictionaries
    """
    if target_date is None:
        target_date = date.today()

    # Get timezone - use system local timezone if not specified
    if timezone_name:
        local_tz = pytz.timezone(timezone_name)
    else:
        local_tz = get_local_timezone()

    # Parse calendar
    try:
        cal = Calendar.from_ical(ics_content)
    except Exception as e:
        print(f"Error parsing iCal: {e}", file=sys.stderr)
        return []

    events = []

    for component in cal.walk():
        if component.name == "VEVENT":
            try:
                # Extract event details
                summary = str(component.get('summary', 'No Title'))
                description = str(component.get('description', ''))
                location = str(component.get('location', ''))

                # Get start and end times
                dtstart = component.get('dtstart')
                dtend = component.get('dtend')

                if dtstart is None:
                    continue

                start_dt = get_event_datetime(dtstart.dt, local_tz)
                end_dt = get_event_datetime(dtend.dt if dtend else None, local_tz)

                # Check if event is on target date
                if isinstance(start_dt, datetime):
                    event_date = start_dt.date()
                else:
                    event_date = start_dt

                # Include events that occur on target date
                # (start on target date OR span across target date)
                is_on_target_date = False

                if event_date == target_date:
                    is_on_target_date = True
                elif end_dt:
                    end_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
                    if event_date <= target_date <= end_date:
                        is_on_target_date = True

                if is_on_target_date:
                    # Determine if all-day event
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
                print(f"Error processing event: {e}", file=sys.stderr)
                continue

    # Sort events by start time
    events.sort(key=lambda x: x['start'])

    return events


def main():
    """Main entry point."""
    # Read .ics content from stdin
    ics_content = sys.stdin.read()

    # Parse arguments (optional: could add date and timezone as args)
    # For now, using today and system timezone
    events = parse_ical(ics_content)

    # Output JSON
    print(json.dumps(events, indent=2))


if __name__ == '__main__':
    main()
