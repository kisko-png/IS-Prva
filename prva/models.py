from dataclasses import dataclass
from typing import Optional

@dataclass
class Lecture:
    lecture_number: int
    class_name: str
    teacher: str
    start_time: Optional[int]
    classroom: Optional[str]
    duration: int


@dataclass
class UnassignedLecture:
    lecture_number: int
    class_name: str
    duration: int