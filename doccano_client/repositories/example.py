from __future__ import annotations

from typing import Iterator, List, Optional
from urllib.parse import urlparse

from doccano_client.models.example import Example
from doccano_client.repositories.base import BaseRepository


class ExampleRepository:
    """Repository for interacting with the Doccano example API"""

    def __init__(self, client: BaseRepository):
        self._client = client

    def find_by_id(self, project_id: int, example_id: int) -> Example:
        """Find a example by id

        Args:
            project_id (int): The id of the project
            example_id (int): The id of the example to find

        Returns:
            Example: The found example
        """
        response = self._client.get(f"projects/{project_id}/examples/{example_id}")
        return Example.parse_obj(response.json())

    def count(self, project_id: int) -> int:
        """Count the number of examples

        Args:
            project_id (int): The id of the project

        Returns:
            int: The number of examples
        """
        response = self._client.get(f"projects/{project_id}/examples")
        return response.json()["count"]

    def list(self, project_id: int, is_confirmed: Optional[bool] = None) -> Iterator[Example]:
        """Return all examples in which you are a member

        Args:
            project_id (int): The id of the project
            is_confirmed (bool, optional): Filter by confirmed state. Defaults to None.

        Yields:
            Example: The next example.
        """
        params = {}
        if is_confirmed is not None:
            params["confirmed"] = is_confirmed
        response = self._client.get(f"projects/{project_id}/examples", params=params)

        while True:
            examples = response.json()
            for example in examples["results"]:
                yield Example.parse_obj(example)

            if examples["next"] is None:
                break
            else:
                next_url = examples["next"]
                response = self._client.get(next_url)
                # If the response we got is not json parseable, most likely the hostname was set wrongly. 
                # This can happen if doccano is hosted behind a reverse proxy. Thus, we use the client's
                # base url
                if not response.headers.get('content-type') == 'application/json': 
                    client_url_parsed = urlparse(self._client._base_url)
                    next_url = urlparse(examples["next"])._replace(scheme=client_url_parsed.scheme, netloc=client_url_parsed.netloc).geturl()
                    response = self._client.get(next_url)

    def create(self, project_id: int, example: Example) -> Example:
        """Create a new example

        Args:
            project_id (int): The id of the project
            example (Example): The example to create

        Returns:
            Example: The created example
        """
        response = self._client.post(f"projects/{project_id}/examples", json=example.dict(exclude={"id"}))
        return Example.parse_obj(response.json())

    def update(self, project_id: int, example: Example) -> Example:
        """Update a example

        Args:
            project_id (int): The id of the project
            example (Example): The example to update

        Returns:
            Example: The updated example
        """
        resource = f"projects/{project_id}/examples/{example.id}"
        response = self._client.put(resource, json=example.dict())
        return Example.parse_obj(response.json())

    def delete(self, project_id: int, example: Example | int):
        """Delete a example

        Args:
            project_id (int): The id of the project
            example (Example | int): The example to delete
        """
        resource = f"projects/{project_id}/examples/{example if isinstance(example, int) else example.id}"
        self._client.delete(resource)

    def delete_all(self, project_id: int):
        """Delete all examples

        Args:
            project_id (int): The id of the project
        """
        examples: List[int] = []
        self.bulk_delete(project_id, examples)

    def bulk_delete(self, project_id: int, examples: List[int] | List[Example]):
        """Bulk delete examples

        Args:
            project_id (int): The id of the project
            examples (List[int] | List[Example]): The list of example ids to delete
        """
        ids = [example if isinstance(example, int) else example.id for example in examples]
        self._client.delete(f"projects/{project_id}/examples", json={"ids": ids})

    def update_state(self, project_id: int, example: Example | int):
        """Update completed state of example

        Args:
            project_id (int): The id of the project
            example (Example | int): The example to confirm
        """
        example_id = example if isinstance(example, int) else example.id
        resource = f"projects/{project_id}/examples/{example_id}/states"
        self._client.post(resource)
