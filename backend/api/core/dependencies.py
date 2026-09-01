from fastapi import Header


def get_api_key(x_api_key: str | None = Header(default=None)) -> str | None:
    return x_api_key
