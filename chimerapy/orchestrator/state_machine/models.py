from typing import List, Optional

from pydantic import BaseModel, Field


class Transition(BaseModel):
    """A transition between two states in a finite state machine."""

    name: str = Field(..., description="The name of the transition.")
    from_state: str = Field(
        ..., description="The name of the state the transition is from."
    )
    to_state: str = Field(
        ..., description="The name of the state the transition is to."
    )

    @property
    def key(self):
        return self.name

    def __repr__(self):
        return (
            f"<Transition({self.name}): {self.from_state} -> {self.to_state}>"
        )


class State(BaseModel):
    """A state in a finite state machine."""

    name: str = Field(..., description="The name of the state.")

    valid_transitions: List[Transition] = Field(
        default_factory=list,
        description="The valid transitions from this state.",
    )

    description: Optional[str] = Field(
        "A state in a finite state machine.",
        description="A description of the state.",
    )

    def __repr__(self):
        return f"<State {self.name}, Valid Transitions: {[t.key + ' -> ' + t.to_state for t in self.valid_transitions]}>"

    def describe(self):
        return f"{self.name}: {self.description}\n{repr(self)}"

    def __hash__(self):
        return hash(self.name)
