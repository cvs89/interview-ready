export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    request_id: string;
  };
}

export type UserRole = "CANDIDATE" | "INTERVIEWER" | "ADMIN";
export type UserStatus = "ACTIVE" | "SUSPENDED" | "DISABLED";

export interface User {
  id: string;
  firebase_uid: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  email_verified: boolean;
  auth_provider?: string | null;
  last_login_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type VerificationStatus = "PENDING" | "IN_REVIEW" | "APPROVED" | "REJECTED";

export interface InterviewerSkill {
  id: string;
  name: string;
  slug: string;
  years_experience?: number | null;
}

export interface InterviewerProfile {
  id: string;
  full_name: string;
  bio?: string | null;
  title?: string | null;
  years_experience?: number | null;
  default_rate_minor?: number | null;
  currency?: string | null;
  linkedin_url?: string | null;
  is_verified: boolean;
  verification_status: VerificationStatus;
  skills: InterviewerSkill[];
}

export interface ParsedProfileDocumentResponse {
  title?: string | null;
  bio?: string | null;
  years_experience?: number | null;
  skills: string[];
  suggested_rate_minor?: number | null;
  suggested_currency?: string | null;
  raw_preview?: string | null;
}

export interface Skill {
  id: string;
  name: string;
  slug: string;
}

export type AvailabilityStatus = "AVAILABLE" | "RESERVED" | "BOOKED" | "BLOCKED";

export interface AvailabilitySlot {
  id: string;
  interviewer_id: string;
  start_time: string;
  end_time: string;
  price_minor: number;
  currency: string;
  status: AvailabilityStatus;
}

export type BookingStatus =
  | "PENDING_PAYMENT"
  | "CONFIRMED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED"
  | "EXPIRED"
  | "NO_SHOW"
  | "REFUNDED";

export interface Booking {
  id: string;
  slot_id: string;
  candidate_id: string;
  interviewer_id: string;
  status: BookingStatus;
  price_minor: number;
  currency: string;
  reservation_expires_at?: string | null;
  created_at: string;
  confirmed_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
}

export interface PaymentCheckoutResponse {
  booking_id: string;
  payment_id: string;
  provider: string;
  amount_minor: number;
  currency: string;
  status: string;
  checkout_url: string;
  provider_checkout_session_id?: string | null;
  expires_at?: string | null;
}

export interface JoinStatusResponse {
  booking_id: string;
  can_join: boolean;
  server_time: string;
  join_available_at: string;
  join_closes_at: string;
  reason?: string | null;
  room_name?: string | null;
}

export interface MintDesktopTicketRequest {
  booking_id: string;
}

export interface MintDesktopTicketResponse {
  ticket: string;
  expires_in_seconds: number;
  join_closes_at: string;
  booking_id: string;
}

export interface ExchangeDesktopTicketResponse {
  session_jwt: string;
  livekit_url: string;
  livekit_token: string;
  room_name: string;
  session_id: string;
  booking_id: string;
  role: string;
  expires_in_seconds: number;
}

export type RubricStatus = "DRAFT" | "SUBMITTED" | "LOCKED";

export interface RubricDraftRequest {
  technical_score?: number | null;
  problem_solving_score?: number | null;
  communication_score?: number | null;
  detailed_feedback?: string | null;
  action_items?: string | null;
  private_interviewer_notes?: string | null;
}

export interface RubricSubmitRequest {
  technical_score: number;
  problem_solving_score: number;
  communication_score: number;
  detailed_feedback: string;
  action_items?: string | null;
  private_interviewer_notes?: string | null;
}

export interface InterviewerRubricResponse {
  id: string;
  booking_id: string;
  interviewer_id: string;
  technical_score?: number | null;
  problem_solving_score?: number | null;
  communication_score?: number | null;
  detailed_feedback?: string | null;
  action_items?: string | null;
  private_interviewer_notes?: string | null;
  status: RubricStatus;
  version: number;
  submitted_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CandidateFeedbackResponse {
  booking_id: string;
  technical_score?: number | null;
  problem_solving_score?: number | null;
  communication_score?: number | null;
  detailed_feedback?: string | null;
  action_items?: string | null;
  submitted_at?: string | null;
  status: RubricStatus;
}

export interface ReviewCreateRequest {
  rating: number;
  review?: string | null;
}

export interface ReviewResponse {
  id: string;
  booking_id: string;
  candidate_id: string;
  interviewer_id: string;
  rating: number;
  review?: string | null;
  created_at: string;
}

export interface InterviewerRatingSummary {
  interviewer_id: string;
  average_rating?: number | null;
  total_reviews: number;
}

export interface InAppNotificationResponse {
  id: string;
  user_id: string;
  event_type: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  read_at?: string | null;
  created_at: string;
}

export interface AuditLogResponse {
  id: string;
  actor_user_id?: string | null;
  event_type: string;
  resource_type: string;
  resource_id: string;
  request_id?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface TaskProcessRequest {
  task_type: string;
  payload?: Record<string, unknown>;
}

export interface TaskProcessResponse {
  status: string;
  task_type: string;
  processed_count: number;
  details: Record<string, unknown>;
}

export interface AdminUserResponse {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  email_verified: boolean;
  auth_provider?: string | null;
  last_login_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminUserListResponse {
  items: AdminUserResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminUserStatusUpdateRequest {
  status: UserStatus;
  reason?: string | null;
}

export interface AdminInterviewerVerificationResponse {
  id: string;
  interviewer_id: string;
  user_id: string;
  full_name: string;
  email: string;
  title?: string | null;
  years_experience?: number | null;
  linkedin_url?: string | null;
  status: string;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  notes?: string | null;
}

export interface AdminVerificationListResponse {
  items: AdminInterviewerVerificationResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminBookingItemResponse {
  id: string;
  slot_id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  interviewer_id: string;
  interviewer_name: string;
  interviewer_email: string;
  status: string;
  cancellation_reason?: string | null;
  slot_start_time: string;
  slot_end_time: string;
  price_minor: number;
  currency: string;
  payment_status?: string | null;
  created_at: string;
}

export interface AdminBookingListResponse {
  items: AdminBookingItemResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminPaymentItemResponse {
  id: string;
  booking_id: string;
  amount_minor: number;
  currency: string;
  provider: string;
  status: string;
  provider_payment_id: string;
  created_at: string;
  updated_at: string;
}

export interface AdminPaymentListResponse {
  items: AdminPaymentItemResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminSlotItemResponse {
  id: string;
  interviewer_id: string;
  interviewer_name: string;
  start_time: string;
  end_time: string;
  price_minor: number;
  currency: string;
  status: string;
  created_at: string;
}

export interface AdminSlotListResponse {
  items: AdminSlotItemResponse[];
  total: number;
  limit: number;
  offset: number;
}

