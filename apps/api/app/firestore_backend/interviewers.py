from datetime import datetime
from typing import Any

from app.core.errors import ApiError
from app.firestore_backend.common import BaseService, audit, key_for, new_doc, now, require_admin
from app.firestore_backend.store import Document, UnitOfWork
from app.schemas.interviewers import ProfileResponse
from app.services.interviewers import InterviewerService as SQLInterviewerService


class InterviewerService(BaseService):
    @staticmethod
    def to_profile_response(profile: Document, *, public: bool = False) -> ProfileResponse:
        result = dict(profile)
        if public:
            short = profile["id"].split("-")[0][:4].upper()
            result["full_name"] = (
                f"{profile.get('title') or 'Technical Interviewer'} • Verified #{short}"
            )
            result["bio"] = SQLInterviewerService.sanitize_public_bio(
                profile.get("bio"), profile["full_name"]
            )
            result["linkedin_url"] = None
        return ProfileResponse.model_validate(result)

    async def owned(self, tx: UnitOfWork, user_id: object) -> Document:
        binding = await tx.require("profile_keys", user_id, "PROFILE_NOT_FOUND")
        return await tx.require("interviewers", binding["profile_id"], "PROFILE_NOT_FOUND")

    async def get_profile_for_user(self, user_id: object) -> Document | None:
        tx = self.store.reader()
        binding = await tx.get("profile_keys", user_id)
        return await tx.get("interviewers", binding["profile_id"]) if binding else None

    async def create_profile(self, user: Any, request: Any) -> ProfileResponse:
        async def operation(tx: UnitOfWork) -> Document:
            if await tx.get("profile_keys", user.id):
                raise ApiError("PROFILE_ALREADY_EXISTS", "Profile already exists.", 409)
            profile = new_doc(
                **request.model_dump(),
                user_id=str(user.id),
                full_name=user.full_name,
                is_verified=False,
                verification_status="PENDING",
                skills=[],
                skill_slugs=[],
            )
            verification = new_doc(
                interviewer_id=profile["id"],
                status="PENDING",
                submitted_at=now(),
                reviewed_at=None,
                reviewed_by=None,
                notes=None,
            )
            tx.put("profile_keys", user.id, {"profile_id": profile["id"]})
            tx.put("interviewers", profile["id"], profile)
            tx.put("verifications", profile["id"], verification)
            return profile

        return self.to_profile_response(await self.store.run(operation))

    async def update_profile(self, user: Any, request: Any) -> ProfileResponse:
        async def operation(tx: UnitOfWork) -> Document:
            profile = await self.owned(tx, user.id)
            profile.update(request.model_dump(exclude_unset=True), updated_at=now())
            tx.put("interviewers", profile["id"], profile)
            return profile

        return self.to_profile_response(await self.store.run(operation))

    async def submit_verification(self, user: Any) -> Document:
        async def operation(tx: UnitOfWork) -> Document:
            profile = await self.owned(tx, user.id)
            verification = await tx.require(
                "verifications", profile["id"], "VERIFICATION_NOT_FOUND"
            )
            if verification["status"] == "APPROVED":
                raise ApiError("ALREADY_APPROVED", "Interviewer is already approved.", 409)
            verification.update(
                status="PENDING", submitted_at=now(), reviewed_at=None, reviewed_by=None, notes=None
            )
            profile.update(is_verified=False, verification_status="PENDING")
            tx.put("interviewers", profile["id"], profile)
            tx.put("verifications", profile["id"], verification)
            return verification

        return await self.store.run(operation)

    async def review_verification(
        self, interviewer_id: object, reviewer: Any, request: Any
    ) -> Document:
        require_admin(reviewer)

        async def operation(tx: UnitOfWork) -> Document:
            profile = await tx.require("interviewers", interviewer_id, "PROFILE_NOT_FOUND")
            verification = await tx.require(
                "verifications", interviewer_id, "VERIFICATION_NOT_FOUND"
            )
            owner = await tx.require("users", profile["user_id"], "USER_NOT_FOUND")
            approved = request.status == "APPROVED"
            verification.update(
                status=str(request.status),
                reviewed_at=now(),
                reviewed_by=str(reviewer.id),
                notes=request.notes,
            )
            profile.update(is_verified=approved, verification_status=str(request.status))
            if owner["role"] != "ADMIN":
                owner["role"] = "INTERVIEWER" if approved else "CANDIDATE"
            tx.put("users", owner["id"], owner)
            tx.put("interviewers", interviewer_id, profile)
            tx.put("verifications", interviewer_id, verification)
            audit(
                tx,
                "INTERVIEWER_VERIFICATION_REVIEWED",
                "INTERVIEWER_PROFILE",
                interviewer_id,
                reviewer.id,
                {"status": str(request.status)},
            )
            return verification

        return await self.store.run(operation)

    async def create_skill(self, request: Any) -> Document:
        async def operation(tx: UnitOfWork) -> Document:
            keys = [key_for("slug", request.slug), key_for("name", request.name.strip().casefold())]
            for key in keys:
                if await tx.get("skill_keys", key):
                    raise ApiError("SKILL_ALREADY_EXISTS", "Skill already exists.", 409)
            doc = new_doc(name=request.name.strip(), slug=request.slug)
            for key in keys:
                tx.put("skill_keys", key, {"skill_id": doc["id"]})
            tx.put("skills", doc["id"], doc)
            return doc

        return await self.store.run(operation)

    async def list_skills(self) -> list[Document]:
        return sorted(await self.scan("skills"), key=lambda s: s["name"])

    async def add_skill(self, user: Any, request: Any) -> ProfileResponse:
        async def operation(tx: UnitOfWork) -> Document:
            profile = await self.owned(tx, user.id)
            skill = await tx.require("skills", request.skill_id, "SKILL_NOT_FOUND")
            skills = [s for s in profile["skills"] if s["id"] != skill["id"]]
            skills.append(
                {k: skill[k] for k in ("id", "name", "slug")}
                | {"years_experience": request.years_experience}
            )
            profile["skills"] = sorted(skills, key=lambda s: s["name"])
            profile["skill_slugs"] = [s["slug"] for s in skills]
            tx.put("interviewers", profile["id"], profile)
            return profile

        return self.to_profile_response(await self.store.run(operation))

    async def remove_skill(self, user: Any, skill_id: object) -> None:
        async def operation(tx: UnitOfWork) -> None:
            profile = await self.owned(tx, user.id)
            skills = [s for s in profile["skills"] if s["id"] != str(skill_id)]
            if len(skills) == len(profile["skills"]):
                raise ApiError("SKILL_NOT_FOUND", "Profile skill not found.", 404)
            profile.update(skills=skills, skill_slugs=[s["slug"] for s in skills])
            tx.put("interviewers", profile["id"], profile)

        await self.store.run(operation)

    async def change_slot(
        self, user: Any, request: Any = None, slot_id: object = None, block: bool = False
    ) -> Document:
        async def operation(tx: UnitOfWork) -> Document:
            profile = await self.owned(tx, user.id)
            if user.role != "INTERVIEWER" or not profile["is_verified"]:
                raise ApiError("INTERVIEWER_NOT_APPROVED", "Approved interviewer required.", 403)
            slot = await tx.require("slots", slot_id, "SLOT_NOT_FOUND") if slot_id else None
            if slot and slot["interviewer_id"] != profile["id"]:
                raise ApiError("SLOT_NOT_FOUND", "Slot not found.", 404)
            if slot and slot["status"] != "AVAILABLE":
                raise ApiError("SLOT_NOT_EDITABLE", "Slot is not available for editing.", 409)
            if slot is None:
                price = request.price_minor
                currency = request.currency
                if price is None:
                    price, currency = profile.get("default_rate_minor"), profile.get("currency")
                if price is None or currency is None:
                    raise ApiError("PRICING_REQUIRED", "Slot pricing is required.", 422)
                slot = new_doc(
                    interviewer_id=profile["id"],
                    start_time=request.start_time,
                    end_time=request.end_time,
                    price_minor=price,
                    currency=currency,
                    status="AVAILABLE",
                    booking_id=None,
                    reserved_by=None,
                    reservation_expires_at=None,
                )
            elif not block:
                slot.update(request.model_dump(exclude_unset=True, exclude_none=True))
            if slot["end_time"] <= slot["start_time"]:
                raise ApiError("INVALID_TIME_RANGE", "Invalid slot interval.", 422)
            # All slot creation/rescheduling touches the same guard. Concurrent
            # empty range queries therefore cannot both commit overlapping slots.
            guard = await tx.get("schedule_guards", profile["id"]) or {"version": 0}
            overlaps = await tx.query(
                "slots",
                (("interviewer_id", "==", profile["id"]), ("end_time", ">", slot["start_time"])),
                limit=self.settings.firestore_scan_limit + 1,
            )
            if len(overlaps) > self.settings.firestore_scan_limit:
                raise ApiError("QUERY_TOO_BROAD", "Schedule exceeds query budget.", 422)
            if not block and any(
                s["id"] != slot["id"] and s["start_time"] < slot["end_time"] for s in overlaps
            ):
                raise ApiError("SLOT_OVERLAP", "This time overlaps another slot.", 409)
            if block:
                slot["status"] = "BLOCKED"
            slot["updated_at"] = now()
            tx.put("schedule_guards", profile["id"], {"version": guard["version"] + 1})
            tx.put("slots", slot["id"], slot)
            audit(
                tx,
                "SLOT_BLOCKED" if block else "SLOT_UPDATED" if slot_id else "SLOT_CREATED",
                "AVAILABILITY_SLOT",
                slot["id"],
                user.id,
            )
            return slot

        return await self.store.run(operation)

    async def create_slot(self, user: Any, request: Any) -> Document:
        return await self.change_slot(user, request)

    async def update_slot(self, user: Any, slot_id: object, request: Any) -> Document:
        return await self.change_slot(user, request, slot_id)

    async def block_slot(self, user: Any, slot_id: object) -> Document:
        return await self.change_slot(user, slot_id=slot_id, block=True)

    async def list_owned_slots(self, user_id: object) -> list[Document]:
        profile = await self.owned(self.store.reader(), user_id)
        return await self.scan("slots", (("interviewer_id", "==", profile["id"]),))

    async def get_public_profile(self, interviewer_id: object) -> Document | None:
        tx = self.store.reader()
        profile = await tx.get("interviewers", interviewer_id)
        if not profile or not profile["is_verified"]:
            return None
        owner = await tx.get("users", profile["user_id"])
        return profile if owner and owner["status"] == "ACTIVE" else None

    async def list_public_slots(self, interviewer_id: object) -> list[Document]:
        if await self.get_public_profile(interviewer_id) is None:
            return []
        slots = await self.scan("slots", (("interviewer_id", "==", str(interviewer_id)),))
        return sorted(
            [s for s in slots if s["status"] == "AVAILABLE" and s["start_time"] > now()],
            key=lambda s: s["start_time"],
        )

    async def list_public_profiles(
        self,
        skill_slug: str | None = None,
        min_years_experience: int | None = None,
        min_price_minor: int | None = None,
        max_price_minor: int | None = None,
        available_from: datetime | None = None,
        available_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        filters: tuple[tuple[str, str, Any], ...] = (("is_verified", "==", True),)
        if skill_slug:
            filters += (("skill_slugs", "array_contains", skill_slug),)
        profiles = await self.scan("interviewers", filters)
        matches = []
        for p in profiles:
            if (
                min_years_experience is not None
                and (p.get("years_experience") or 0) < min_years_experience
            ):
                continue
            if await self.get_public_profile(p["id"]) is None:
                continue
            if any(
                v is not None
                for v in (
                    min_price_minor,
                    max_price_minor,
                    available_from,
                    available_to,
                )
            ):
                slots = await self.list_public_slots(p["id"])
                if not any(
                    (not available_from or s["end_time"] > available_from)
                    and (not available_to or s["start_time"] < available_to)
                    and (min_price_minor is None or s["price_minor"] >= min_price_minor)
                    and (max_price_minor is None or s["price_minor"] <= max_price_minor)
                    for s in slots
                ):
                    continue
            matches.append(p)
        return sorted(matches, key=lambda p: p["id"])[offset : offset + limit]
