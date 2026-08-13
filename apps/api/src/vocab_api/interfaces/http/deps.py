from fastapi import Request

from vocab_api.config.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container
