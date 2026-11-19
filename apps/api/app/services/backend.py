"""Select persistence per application, never via a process-global environment switch.

The SQL implementation remains available for existing deployments and migration
verification. Only the API composition layer imports these factories.
"""

from typing import Any, TypeVar, cast

from app.firestore_backend import bookings, feedback, identity, interviewers, operations, sessions
from app.firestore_backend.store import FirestoreStore
from app.repositories.interviewers import InterviewerRepository as SQLInterviewerRepository
from app.services.admin import AdminService as SQLAdminService
from app.services.audit import AuditService as SQLAuditService
from app.services.bookings import BookingService as SQLBookingService
from app.services.bookings import PaymentService as SQLPaymentService
from app.services.feedback import ReviewService as SQLReviewService
from app.services.feedback import RubricService as SQLRubricService
from app.services.identity import IdentityService as SQLIdentityService
from app.services.interviewers import InterviewerService as SQLInterviewerService
from app.services.notification import NotificationService as SQLNotificationService
from app.services.sessions import DesktopAuthService as SQLDesktopAuthService
from app.services.tasks import TaskService as SQLTaskService

T = TypeVar("T")


def factory(sql: type[T], firestore: Any) -> type[T]:
    def build(session: Any, *args: Any, **kwargs: Any) -> Any:
        implementation: Any = firestore if isinstance(session, FirestoreStore) else sql
        return implementation(session, *args, **kwargs)

    # Firestore dictionaries are validated by API response models at the boundary.
    # Retain the existing service interface during the dual-backend migration.
    return cast(type[T], build)


IdentityService = factory(SQLIdentityService, identity.IdentityService)
BookingService = factory(SQLBookingService, bookings.BookingService)
PaymentService = factory(SQLPaymentService, bookings.PaymentService)
DesktopAuthService = factory(SQLDesktopAuthService, sessions.DesktopAuthService)
RubricService = factory(SQLRubricService, feedback.RubricService)
ReviewService = factory(SQLReviewService, feedback.ReviewService)
AdminService = factory(SQLAdminService, operations.AdminService)
AuditService = factory(SQLAuditService, operations.AuditService)
NotificationService = factory(SQLNotificationService, operations.NotificationService)
TaskService = factory(SQLTaskService, operations.TaskService)
InterviewerRepository = factory(SQLInterviewerRepository, interviewers.InterviewerService)
InterviewerService = factory(SQLInterviewerService, interviewers.InterviewerService)


def profile_response(profile: Any, *, public: bool = False) -> Any:
    implementation = (
        interviewers.InterviewerService if isinstance(profile, dict) else SQLInterviewerService
    )
    return implementation.to_profile_response(profile, public=public)


cast(Any, InterviewerService).to_profile_response = profile_response
