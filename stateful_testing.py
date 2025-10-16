from hypothesis import given, strategies as st, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize, Bundle, precondition
from hypothesis.core import FailedHealthCheck
from typing import List, Optional
import sys
import io
import unittest


class FIFOBuffer:
    """A FIFO buffer with a maximum length constraint."""
    
    def __init__(self, max_length: int):
        if max_length <= 0:
            raise ValueError("max_length must be positive")
        self.max_length = max_length
        self.buffer: List[int] = []
    
    def add(self, item: int) -> None:
        """Add an item to the buffer."""
        if len(self.buffer) >= self.max_length:
            # Remove oldest item if buffer is full
            self.buffer.pop(0)
        self.buffer.append(item)
    
    def remove(self) -> Optional[int]:
        """Remove and return the oldest item from the buffer."""
        if not self.buffer:
            return None
        return self.buffer.pop(0)
    
    def peek(self) -> Optional[int]:
        """Return the oldest item without removing it."""
        if not self.buffer:
            return None
        return self.buffer[0]
    
    def is_empty(self) -> bool:
        """Check if the buffer is empty."""
        return len(self.buffer) == 0
    
    def is_full(self) -> bool:
        """Check if the buffer is at maximum capacity."""
        return len(self.buffer) == self.max_length
    
    def size(self) -> int:
        """Return the current number of items in the buffer."""
        return len(self.buffer)


class BrokenFIFOBuffer:
    """A BROKEN FIFO buffer that violates invariants for testing purposes."""
    
    def __init__(self, max_length: int):
        # BUG 1: No validation of negative max_length
        self.max_length = max_length
        self.buffer: List[int] = []
    
    def add(self, item: int) -> None:
        """Add an item to the buffer."""
        # BUG 2: No max_length check - can grow indefinitely
        self.buffer.append(item)
    
    def remove(self) -> Optional[int]:
        """Remove and return the oldest item from the buffer."""
        # BUG 3: No empty check - will crash on empty buffer
        return self.buffer.pop(0)
    
    def peek(self) -> Optional[int]:
        """Return the oldest item without removing it."""
        # BUG 4: No empty check - will crash on empty buffer
        return self.buffer[0]
    
    def is_empty(self) -> bool:
        """Check if the buffer is empty."""
        return len(self.buffer) == 0
    
    def is_full(self) -> bool:
        """Check if the buffer is at maximum capacity."""
        return len(self.buffer) == self.max_length
    
    def size(self) -> int:
        """Return the current number of items in the buffer."""
        return len(self.buffer)


class FIFOBufferStateMachine(RuleBasedStateMachine):
    """Stateful test machine for FIFO buffer operations."""
    
    def __init__(self):
        super().__init__()
        self.buffer: Optional[FIFOBuffer] = None
        self.max_length: int = 0
    
    @rule(max_length=st.integers(min_value=1, max_value=10))
    def initialize_buffer(self, max_length: int):
        """Initialize a new buffer with given max_length."""
        self.max_length = max_length
        self.buffer = FIFOBuffer(max_length)
    
    @rule(item=st.integers())
    def add_item(self, item: int):
        """Add an item to the buffer."""
        if self.buffer is not None:
            self.buffer.add(item)
    
    @rule()
    def remove_item(self):
        """Remove an item from the buffer."""
        if self.buffer is not None:
            self.buffer.remove()
    
    @rule()
    def peek_item(self):
        """Peek at the oldest item without removing it."""
        if self.buffer is not None:
            self.buffer.peek()
    
    @rule()
    def check_empty(self):
        """Check if buffer is empty."""
        if self.buffer is not None:
            self.buffer.is_empty()
    
    @rule()
    def check_full(self):
        """Check if buffer is full."""
        if self.buffer is not None:
            self.buffer.is_full()
    
    @rule()
    def check_size(self):
        """Check buffer size."""
        if self.buffer is not None:
            self.buffer.size()
    
    @invariant()
    def buffer_length_invariant(self):
        """Invariant: buffer length must be <= max_length."""
        if self.buffer is not None:
            assert self.buffer.size() <= self.max_length, \
                f"Buffer size {self.buffer.size()} exceeds max_length {self.max_length}"
    
    @invariant()
    def buffer_not_negative(self):
        """Invariant: buffer size should never be negative."""
        if self.buffer is not None:
            assert self.buffer.size() >= 0, \
                f"Buffer size {self.buffer.size()} is negative"



class BrokenFIFOBufferStateMachine(RuleBasedStateMachine):
    """Stateful test machine for BROKEN FIFO buffer operations."""

    def __init__(self):
        super().__init__()
        self.buffer_map = {}
    Buffer_Keys = Bundle("buffer_keys")

    @rule(target=Buffer_Keys, max_length=st.integers(min_value=-1, max_value=10))
    def initialize_buffer(self, max_length: int):
        """Initialize a new buffer with given max_length."""
        if max_length not in self.buffer_map:
            self.buffer_map[max_length] = BrokenFIFOBuffer(max_length)
        return max_length

    # @precondition(lambda self: len(self.buffer_map.keys()) > 0)
    @rule(item=st.integers(), buffer_key=Buffer_Keys)
    def add_item(self, item: int, buffer_key: int):
        """Add an item to the buffer."""
        self.buffer_map[buffer_key].add(item)
    
    # @precondition(lambda self: len(self.buffer_map.keys()) > 0)
    @rule(buffer_key=Buffer_Keys)
    def check_empty(self, buffer_key: int):
        """Check if buffer is empty."""
        self.buffer_map[buffer_key].is_empty()
    
    # @precondition(lambda self: len(self.buffer_map.keys()) > 0)
    @rule(buffer_key=Buffer_Keys)
    def check_full(self, buffer_key: int):
        """Check if buffer is full."""
        self.buffer_map[buffer_key].is_full()
    
    # @precondition(lambda self: len(self.buffer_map.keys()) > 0)
    @rule(buffer_key=Buffer_Keys)
    def check_size(self, buffer_key: int):
        """Check buffer size."""
        self.buffer_map[buffer_key].size()
    
    @precondition(lambda self: len(self.buffer_map.keys()) > 0)
    @invariant()
    def buffer_length_invariant(self):
        """Invariant: buffer length must be <= max_length."""
        for buffer_key in self.buffer_map:
            assert self.buffer_map[buffer_key].size() <= self.buffer_map[buffer_key].max_length, \
                f"Buffer size {self.buffer_map[buffer_key].size()} exceeds max_length {self.buffer_map[buffer_key].max_length}"
        
    @precondition(lambda self: len(self.buffer_map.keys()) > 0)
    @invariant()
    def buffer_not_negative(self):
        """Invariant: buffer size should never be negative."""
        for buffer_key in self.buffer_map:
            assert self.buffer_map[buffer_key].size() >= 0, \
                f"Buffer size {self.buffer_map[buffer_key].size()} is negative"
    
    @precondition(lambda self: len(self.buffer_map.keys()) > 0)
    @invariant()
    def max_length_positive(self):
        """Invariant: max_length should be positive."""
        for buffer_key in self.buffer_map:
            assert self.buffer_map[buffer_key].max_length > 0, \
                f"max_length {self.buffer_map[buffer_key].max_length} should be positive"

# Test the stateful machines with more aggressive settings
TestFIFOBuffer = FIFOBufferStateMachine.TestCase

# Apply settings to make tests more thorough
TestBrokenFIFOBuffer = BrokenFIFOBufferStateMachine.TestCase


if __name__ == "__main__":
    # unittest.main(TestFIFOBuffer())
    unittest.main(TestBrokenFIFOBuffer())