import json
from dataclasses import dataclass
from typing import Iterable

from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event, EventSource
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.storage.files import FileStore
from openhands.storage.locations import (
    get_conversation_dir,
)
from openhands.utils.shutdown_listener import should_continue


@dataclass
class EventStore:
    """
    A stored list of events backing a conversation
    """

    sid: str
    file_store: FileStore
    user_id: str | None
    cur_id: int = -1  # We fix this in post init if it is not specified

    def __post_init__(self) -> None:
        if self.cur_id < 0:
            self.cur_id = 0

    def _get_events_log_filename(self) -> str:
        """Gets the path for the events log file."""
        return f'{get_conversation_dir(self.sid, self.user_id)}events.jsonl'

    def get_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter_out_type: tuple[type[Event], ...] | None = None,
        filter_hidden: bool = False,
    ) -> Iterable[Event]:
        """
        Retrieve events from the event stream log file.
        NOTE: Efficient reverse iteration is not yet implemented.
        """

        def should_filter(event: Event) -> bool:
            if filter_hidden and hasattr(event, 'hidden') and event.hidden:
                return True
            if filter_out_type is not None and isinstance(event, filter_out_type):
                return True
            return False

        if reverse:
            logger.warning('Reverse event reading is currently inefficient for large histories.')
            all_events = list(self.get_events(start_id, end_id, False, filter_out_type, filter_hidden))
            yield from reversed(all_events)
            return

        # Determine the exclusive end ID. If None, read all.
        read_to_end = end_id is None
        effective_end_id = float('inf') if read_to_end else end_id + 1

        try:
            log_filename = self._get_events_log_filename()
            full_content = self.file_store.read(log_filename)
            lines = full_content.splitlines()

            current_line_number = 0
            for line in lines:
                if not line.strip():
                    current_line_number += 1 # Still count empty lines for reference
                    continue

                if not should_continue():
                    return

                try:
                    data = json.loads(line)
                    event = event_from_dict(data)
                    actual_event_id = event.id

                    # Check if the ACTUAL event ID is within the desired range
                    if start_id <= actual_event_id < effective_end_id:
                        if not should_filter(event):
                             yield event
                    # OPTIONAL: Add a check to break early if we know IDs are monotonic increasing
                    # and we have passed the effective_end_id, but this assumes
                    # IDs are always in order, which might be broken by resets.
                    # For now, read all lines to handle potential out-of-order IDs due to resets.
                    # if not read_to_end and actual_event_id >= effective_end_id:
                    #    pass # Potentially break if we can guarantee order

                except json.JSONDecodeError:
                    logger.warning(f'Failed to decode JSON in {log_filename} at line {current_line_number+1}')
                except AttributeError:
                     logger.warning(f'Parsed data in {log_filename} at line {current_line_number+1} is not a valid event (missing id?).')
                except Exception as e:
                    logger.error(f'Error processing event in {log_filename} at line {current_line_number+1}: {e}')

                current_line_number += 1

        except FileNotFoundError:
            logger.debug(f'Events log file not found: {log_filename}')
            pass
        except Exception as e:
            logger.error(f'Error reading events log file {log_filename}: {e}')
            pass

    def get_event(self, id: int) -> Event:
        """Gets a single event by its ID."""
        # This will read the stream until the event is found.
        # Potentially inefficient if called frequently for random IDs.
        try:
            # Get an iterator for the single event ID range
            event_iterator = self.get_events(start_id=id, end_id=id)
            # Return the first (and only) event found
            return next(event_iterator)
        except StopIteration:
            raise FileNotFoundError(f'Event with ID {id} not found in log.')
        except Exception as e:
             # Catch other potential errors from get_events
             logger.error(f'Error retrieving event ID {id}: {e}')
             raise

    def get_latest_event(self) -> Event:
        return self.get_event(self.cur_id - 1)

    def get_latest_event_id(self) -> int:
        return self.cur_id - 1

    def filtered_events_by_source(self, source: EventSource) -> Iterable[Event]:
        for event in self.get_events():
            if event.source == source:
                yield event

    def _should_filter_event(
        self,
        event: Event,
        query: str | None = None,
        event_types: tuple[type[Event], ...] | None = None,
        source: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> bool:
        """Check if an event should be filtered out based on the given criteria.

        Args:
            event: The event to check
            query: Text to search for in event content
            event_type: Filter by event type classes (e.g., (FileReadAction, ) ).
            source: Filter by event source
            start_date: Filter events after this date (ISO format)
            end_date: Filter events before this date (ISO format)

        Returns:
            bool: True if the event should be filtered out, False if it matches all criteria
        """
        if event_types and not isinstance(event, event_types):
            return True

        if source:
            if event.source is None or event.source.value != source:
                return True

        if start_date and event.timestamp is not None and event.timestamp < start_date:
            return True

        if end_date and event.timestamp is not None and event.timestamp > end_date:
            return True

        # Text search in event content if query provided
        if query:
            event_dict = event_to_dict(event)
            event_str = json.dumps(event_dict).lower()
            if query.lower() not in event_str:
                return True

        return False

    def get_matching_events(
        self,
        query: str | None = None,
        event_types: tuple[type[Event], ...] | None = None,
        source: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        start_id: int = 0,
        limit: int = 100,
        reverse: bool = False,
    ) -> list[Event]:
        """Get matching events from the event stream based on filters.

        Args:
            query: Text to search for in event content
            event_types: Filter by event type classes (e.g., (FileReadAction, ) ).
            source: Filter by event source
            start_date: Filter events after this date (ISO format)
            end_date: Filter events before this date (ISO format)
            start_id: Starting ID in the event stream. Defaults to 0
            limit: Maximum number of events to return. Must be between 1 and 100. Defaults to 100
            reverse: Whether to retrieve events in reverse order. Defaults to False.

        Returns:
            list: List of matching events (as dicts)

        Raises:
            ValueError: If limit is less than 1 or greater than 100
        """
        if limit < 1 or limit > 100:
            raise ValueError('Limit must be between 1 and 100')

        matching_events: list = []

        for event in self.get_events(start_id=start_id, reverse=reverse):
            if self._should_filter_event(
                event, query, event_types, source, start_date, end_date
            ):
                continue

            matching_events.append(event)

            # Stop if we have enough events
            if len(matching_events) >= limit:
                break

        return matching_events
