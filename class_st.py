from hypothesis import given, strategies as st
from dataclasses import dataclass

# Define a simple dummy class
@dataclass
class Person:
    name: str
    age: int

# Create a strategy to generate Person instances
person_strategy = st.builds(
    Person,
    name=st.text(min_size=1, max_size=10),
    age=st.integers()
)

# Function that takes a Person as input
def greet_person(person):
    return f"Hello {person.name}, you are {person.age} years old!"

# Property-based test using the strategy
@given(person=person_strategy)
def test_greet_person(person):
    greeting = greet_person(person)
    assert person.name in greeting
    assert str(person.age) in greeting
    assert person.age >= 0
    assert person.name.isalpha()
    print(f"Generated: {person} -> {greeting}")


if __name__ == "__main__":
    # Run the test
    test_greet_person()
