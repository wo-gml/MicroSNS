from pydantic import BaseModel


class HashtagStat(BaseModel):
    name: str
    post_count: int
