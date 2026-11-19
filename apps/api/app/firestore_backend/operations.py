import uuid
from typing import Any

from app.core.errors import ApiError
from app.firestore_backend.bookings import BookingService
from app.firestore_backend.common import (
    BaseService,
    audit,
    authorize,
    notify,
    now,
    require_admin,
)
from app.firestore_backend.store import Document, UnitOfWork
from app.schemas.notification import TaskProcessResponse


class AdminService(BaseService):
    @staticmethod
    def page(docs: list[Document], limit: int, offset: int) -> Document:
        return {
            "items": docs[offset : offset + limit],
            "total": len(docs),
            "limit": limit,
            "offset": offset,
        }

    async def list_users(
        self,
        search: str | None = None,
        role: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Document:
        filters = tuple((k, "==", str(v)) for k, v in {"role": role, "status": status}.items() if v)
        docs = await self.scan("users", filters)
        if search:
            docs = [
                d for d in docs if search.casefold() in f"{d['email']} {d['full_name']}".casefold()
            ]
        return self.page(sorted(docs, key=lambda d: d["created_at"], reverse=True), limit, offset)

    async def get_user(self, user_id: object) -> Document:
        return await self.store.reader().require("users", user_id, "USER_NOT_FOUND")

    async def update_user_status(self, user_id: object, admin: Any, request: Any) -> Document:
        require_admin(admin)
        if str(user_id) == str(admin.id):
            raise ApiError("CANNOT_MODIFY_SELF", "Cannot change your own account status.", 400)

        async def operation(tx: UnitOfWork) -> Document:
            doc = await tx.require("users", user_id, "USER_NOT_FOUND")
            doc.update(status=str(request.status), updated_at=now())
            tx.put("users", user_id, doc)
            audit(
                tx,
                "USER_STATUS_UPDATED",
                "USER",
                user_id,
                admin.id,
                {"status": str(request.status), "reason": request.reason},
            )
            return doc

        return await self.store.run(operation)

    async def list_verifications(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> Document:
        docs = await self.scan("verifications", (("status", "==", status),) if status else ())
        reader = self.store.reader()
        results = []
        for doc in docs:
            profile = await reader.require(
                "interviewers", doc["interviewer_id"], "PROFILE_NOT_FOUND"
            )
            user = await reader.require("users", profile["user_id"], "USER_NOT_FOUND")
            results.append(
                {
                    **doc,
                    "user_id": user["id"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "title": profile.get("title"),
                    "years_experience": profile.get("years_experience"),
                    "linkedin_url": profile.get("linkedin_url"),
                }
            )
        return self.page(results, limit, offset)

    async def booking_detail(self, booking: Document) -> Document:
        tx = self.store.reader()
        candidate = await tx.require("users", booking["candidate_id"], "USER_NOT_FOUND")
        interviewer = await tx.require("users", booking["interviewer_id"], "USER_NOT_FOUND")
        slot = await tx.require("slots", booking["slot_id"], "SLOT_NOT_FOUND")
        payment = await tx.get("payments", booking["id"])
        return {
            **booking,
            "candidate_name": candidate["full_name"],
            "candidate_email": candidate["email"],
            "interviewer_name": interviewer["full_name"],
            "interviewer_email": interviewer["email"],
            "slot_start_time": slot["start_time"],
            "slot_end_time": slot["end_time"],
            "payment_status": (payment or {}).get("status"),
        }

    async def get_booking_detail(self, booking_id: object) -> Document:
        return await self.booking_detail(
            await self.store.reader().require("bookings", booking_id, "BOOKING_NOT_FOUND")
        )

    async def list_bookings(
        self,
        status: str | None = None,
        candidate_id: object = None,
        interviewer_id: object = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Document:
        filters = tuple(
            (k, "==", str(v))
            for k, v in {
                "status": status,
                "candidate_id": candidate_id,
                "interviewer_id": interviewer_id,
            }.items()
            if v is not None
        )
        docs = await self.scan("bookings", filters)
        page = self.page(sorted(docs, key=lambda d: d["created_at"], reverse=True), limit, offset)
        page["items"] = [await self.booking_detail(d) for d in page["items"]]
        return page

    async def list_payments(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> Document:
        docs = await self.scan("payments", (("status", "==", status),) if status else ())
        docs = [{**d, "provider_payment_id": d.get("provider_payment_id") or ""} for d in docs]
        return self.page(docs, limit, offset)

    async def list_slots(
        self,
        interviewer_id: object = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Document:
        filters = tuple(
            (k, "==", str(v))
            for k, v in {
                "interviewer_id": interviewer_id,
                "status": status,
            }.items()
            if v is not None
        )
        page = self.page(await self.scan("slots", filters), limit, offset)
        for doc in page["items"]:
            profile = await self.store.reader().require(
                "interviewers", doc["interviewer_id"], "PROFILE_NOT_FOUND"
            )
            doc["interviewer_name"] = profile["full_name"]
        return page


class AuditService(BaseService):
    async def list_logs(
        self,
        user: Any,
        resource_type: str | None = None,
        resource_id: str | None = None,
        actor_user_id: object = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        require_admin(user)
        filters = tuple(
            (k, "==", str(v))
            for k, v in {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "actor_user_id": actor_user_id,
                "event_type": event_type,
            }.items()
            if v is not None
        )
        docs = await self.scan("audit", filters)
        return sorted(docs, key=lambda d: d["created_at"], reverse=True)[offset : offset + limit]


class NotificationService(BaseService):
    async def list_in_app_notifications(
        self, user: Any, unread_only: bool = False, limit: int = 50, offset: int = 0
    ) -> list[Document]:
        filters: tuple[tuple[str, str, Any], ...] = (("user_id", "==", str(user.id)),)
        if unread_only:
            filters += (("read_at", "==", None),)
        return await self.store.reader().query(
            "notifications", filters, order="-created_at", limit=limit, offset=offset
        )

    async def mark_as_read(self, user: Any, notification_id: object) -> bool:
        async def operation(tx: UnitOfWork) -> bool:
            doc = await tx.require("notifications", notification_id, "NOTIFICATION_NOT_FOUND")
            authorize(user, doc, "user_id", admin=False)
            if doc.get("read_at"):
                return False
            doc["read_at"] = now()
            tx.put("notifications", notification_id, doc)
            return True

        return await self.store.run(operation)

    async def mark_all_as_read(self, user: Any) -> int:
        docs = await self.scan(
            "notifications", (("user_id", "==", str(user.id)), ("read_at", "==", None))
        )
        count = 0
        for doc in docs:
            count += int(await self.mark_as_read(user, doc["id"]))
        return count


class TaskService(BaseService):
    async def process_task(self, task_type: str, payload: Document) -> TaskProcessResponse:
        task_type = task_type.strip().lower()
        count = 0
        if task_type == "expire_reservations":
            count = await BookingService(self.store).expire_stale_reservations()
        elif task_type == "dispatch_notification":
            try:
                user_id = str(uuid.UUID(payload["recipient_user_id"]))
            except (KeyError, ValueError, TypeError):
                raise ApiError("INVALID_PAYLOAD", "Recipient user ID required.", 400) from None

            async def operation(tx: UnitOfWork) -> None:
                await tx.require("users", user_id, "USER_NOT_FOUND")
                await notify(
                    tx,
                    payload.get("event_type", "GENERAL"),
                    user_id,
                    str(payload.get("reference_id", "none")),
                    payload.get("title", "Notification"),
                    payload.get("body", ""),
                    payload.get("data", {}),
                    channels=payload.get("channels"),
                )

            await self.store.run(operation)
            count = 1
        elif task_type in ("send_reminders", "post_interview_reminders"):
            status = "CONFIRMED" if task_type == "send_reminders" else "COMPLETED"
            docs = await self.scan("bookings", (("status", "==", status),))
            for doc in docs:
                slot = await self.store.reader().require("slots", doc["slot_id"], "SLOT_NOT_FOUND")
                seconds = (slot["start_time"] - now()).total_seconds()
                event = None
                if task_type == "post_interview_reminders":
                    if not await self.store.reader().get("reviews", doc["id"]):
                        event = "REVIEW_REMINDER"
                elif 23 * 3600 <= seconds <= 24.25 * 3600:
                    event = "REMINDER_24H"
                elif 50 * 60 <= seconds <= 70 * 60:
                    event = "REMINDER_1H"
                elif 0 <= seconds <= 15 * 60:
                    event = "REMINDER_10M"
                if not event:
                    continue

                async def reminder(
                    tx: UnitOfWork, doc: Document = doc, event: str = str(event)
                ) -> None:
                    current = await tx.require("bookings", doc["id"], "BOOKING_NOT_FOUND")
                    if current["status"] != status:
                        return
                    recipients = [doc["candidate_id"]]
                    if status == "CONFIRMED":
                        recipients.append(doc["interviewer_id"])
                    for recipient in recipients:
                        await notify(
                            tx,
                            str(event),
                            recipient,
                            doc["id"],
                            "Interview reminder" if status == "CONFIRMED" else "Leave a review",
                            data={"booking_id": doc["id"]},
                        )

                await self.store.run(reminder)
                count += 1
        elif task_type == "process_refunds":
            count = await self.process_refunds()
        else:
            raise ApiError("UNKNOWN_TASK_TYPE", "Unknown task type.", 400)
        return TaskProcessResponse(task_type=task_type, processed_count=count)

    async def process_refunds(self) -> int:
        from app.firestore_backend.bookings import PaymentService, release

        jobs = await self.store.reader().query(
            "refund_jobs", (("status", "==", "PENDING"),), limit=50
        )
        count = 0
        for job in jobs:
            if not job.get("provider_payment_id"):
                continue
            provider = PaymentService(self.store).provider(job["provider"])
            # Safe across duplicate workers: provider receives stable idempotency key.
            result = await provider.refund(
                provider_payment_id=job["provider_payment_id"],
                amount_minor=job["amount_minor"],
                currency=job["currency"],
                reason="requested_by_customer",
                idempotency_key=job["idempotency_key"],
            )
            if result.status != "succeeded":
                continue

            async def finish(tx: UnitOfWork, job: Document = job, result: Any = result) -> None:
                current = await tx.require("refund_jobs", job["id"], "REFUND_NOT_FOUND")
                payment = await tx.require("payments", job["booking_id"], "PAYMENT_NOT_FOUND")
                booking = await tx.require("bookings", job["booking_id"], "BOOKING_NOT_FOUND")
                slot = await tx.require("slots", booking["slot_id"], "SLOT_NOT_FOUND")
                current.update(status="COMPLETED", refund_id=result.refund_id, updated_at=now())
                payment.update(status="REFUNDED", refunded_at=now())
                await release(tx, booking, slot, "REFUNDED")
                tx.put("payments", job["booking_id"], payment)
                tx.put("refund_jobs", job["id"], current)
                audit(tx, "PAYMENT_REFUNDED", "PAYMENT", payment["id"])

            await self.store.run(finish)
            count += 1
        return count
