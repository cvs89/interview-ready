"""Async Firestore adapter with buffered writes and retryable transactions.

Business callbacks must not perform network side effects. Buffering ensures all
Firestore reads precede writes, including reads made after a domain update.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from copy import deepcopy
from typing import Any, TypeVar

from google.api_core.exceptions import Aborted
from google.cloud.firestore_v1 import AsyncClient, async_transactional
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import ApiError

T = TypeVar("T")
Document = dict[str, Any]


class UnitOfWork:
    def __init__(self, store: "FirestoreStore", transaction: Any = None) -> None:
        self.store = store
        self.transaction = transaction
        self.pending: dict[tuple[str, str], Document | None] = {}

    async def get(self, collection: str, key: object) -> Document | None:
        address = (collection, str(key))
        if address in self.pending:
            return deepcopy(self.pending[address])
        snapshot = (
            await self.store.client.collection(collection)
            .document(str(key))
            .get(transaction=self.transaction)
        )
        return snapshot.to_dict() if snapshot.exists else None

    async def require(self, collection: str, key: object, code: str) -> Document:
        document = await self.get(collection, key)
        if document is None:
            raise ApiError(code, "The requested resource was not found.", 404)
        return document

    async def query(
        self,
        collection: str,
        filters: tuple[tuple[str, str, Any], ...] = (),
        *,
        limit: int = 100,
        offset: int = 0,
        order: str | None = None,
    ) -> list[Document]:
        query: Any = self.store.client.collection(collection)
        for field, operator, value in filters:
            query = query.where(filter=FieldFilter(field, operator, value))
        if order:
            query = query.order_by(
                order.lstrip("-"),
                direction=("DESCENDING" if order.startswith("-") else "ASCENDING"),
            )
        query = query.offset(offset).limit(limit)
        return [s.to_dict() async for s in query.stream(transaction=self.transaction)]

    def put(self, collection: str, key: object, document: Document) -> None:
        self.pending[(collection, str(key))] = deepcopy(document)

    def delete(self, collection: str, key: object) -> None:
        self.pending[(collection, str(key))] = None

    def flush(self) -> None:
        for (collection, key), document in self.pending.items():
            reference = self.store.client.collection(collection).document(key)
            if document is None:
                self.transaction.delete(reference)
            else:
                self.transaction.set(reference, document)


class FirestoreStore:
    def __init__(self, client: AsyncClient, settings: Any) -> None:
        self.client = client
        self.settings = settings

    def reader(self) -> UnitOfWork:
        return UnitOfWork(self)

    async def run(self, callback: Callable[[UnitOfWork], Awaitable[T]]) -> T:
        @async_transactional
        async def execute(transaction: Any) -> T:
            unit = UnitOfWork(self, transaction)
            result = await callback(unit)
            unit.flush()
            return result

        # The SDK retries commit conflicts, but read-time Aborted errors and
        # exhausted lock-upgrade attempts can escape. Retry the whole callback
        # with jitter; never retry business/validation errors or external effects.
        for attempt in range(4):
            try:
                return await execute(self.client.transaction(max_attempts=3))
            except (Aborted, ValueError) as exc:
                if not isinstance(exc, Aborted) and not isinstance(exc.__cause__, Aborted):
                    raise
                if attempt == 3:
                    raise ApiError(
                        "TRANSACTION_BUSY",
                        "Concurrent update; retry the request.",
                        409,
                        headers={"Retry-After": "1"},
                    ) from exc
                await asyncio.sleep(random.uniform(0.05, 0.2) * (2**attempt))
        raise AssertionError("Unreachable")

    async def ping(self) -> None:
        await self.client.collection("_health").document("readiness").get(timeout=5)

    async def close(self) -> None:
        # google-cloud-firestore's client close is synchronous.
        client: Any = self.client
        client.close()
