from pydantic import BaseModel, Field
from typing import List, Optional

class BookSummary(BaseModel):
    title: str = Field(description="The title of the book")
    summary: str = Field(description="A comprehensive summary of the book")
    key_points: List[str] = Field(default_factory=list, description="Key takeaways from the book")
    themes: List[str] = Field(default_factory=list, description="Main themes discussed in the book")
    author: Optional[str] = Field(default=None, description="Author of the book if mentioned")
    genre: Optional[str] = Field(default=None, description="Genre or category of the book")
    word_count: Optional[int] = Field(default=None, description="Approximate word count of the summary")
