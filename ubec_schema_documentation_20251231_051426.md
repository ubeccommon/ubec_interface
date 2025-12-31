# UBEC Protocol - Database Schema Documentation

> **Single Source of Truth** | *"I am because we are"*

---

## Metadata

| Property | Value |
|----------|-------|
| Generated | 2025-12-31T05:14:26.066741 |
| Database | `ubec_ui_interface` |
| Size | 9793 kB |
| PostGIS | ❌ |

## The Four Elements

| Element | Symbol | Token | Principle |
|---------|--------|-------|----------|
| Air | 🜁 | UBEC | Diversity |
| Water | 🜄 | UBECrc | Reciprocity |
| Earth | 🜃 | UBECgpi | Mutualism |
| Fire | 🜂 | UBECtt | Regeneration |

## Summary

| Metric | Count |
|--------|-------|
| Total Schemas | 1 |
| Total Tables | 11 |
| Total Columns | 118 |
| Total Relationships | 5 |
| Total Indexes | 48 |
| Spatial Tables | 0 |
| Ubec Core Tables | 1 |

---

## Schema: `ubec_ui`

### activity_log

**Category:** `other` | **Rows:** 5 | **Size:** 96 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.activity |
| `user_id` | integer | ✓ | - |
| `action` | varchar(100) | ✗ | - |
| `entity_type` | varchar(50) | ✓ | - |
| `entity_id` | integer | ✓ | - |
| `details` | jsonb | ✓ | - |
| `ip_address` | inet | ✓ | - |
| `user_agent` | text | ✓ | - |
| `created_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### announcements

**Category:** `other` | **Rows:** 1 | **Size:** 64 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.announce |
| `title` | varchar(255) | ✗ | - |
| `content` | text | ✗ | - |
| `announcement_type` | varchar(50) | ✓ | 'info'::character varying |
| `is_active` | boolean | ✓ | true |
| `display_from` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |
| `display_until` | timestamp with time zone | ✓ | - |
| `created_by` | varchar(255) | ✓ | - |
| `created_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |
| `updated_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### application_documents

**Category:** `ui` | **Rows:** 0 | **Size:** 24 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.applicat |
| `application_id` | integer | ✗ | - |
| `document_type` | varchar(100) | ✗ | - |
| `filename` | varchar(255) | ✗ | - |
| `file_path` | varchar(500) | ✗ | - |
| `file_size` | integer | ✓ | - |
| `mime_type` | varchar(100) | ✓ | - |
| `uploaded_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |
| `uploaded_by` | varchar(255) | ✓ | - |

### application_status_history

**Category:** `ui` | **Rows:** 0 | **Size:** 32 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.applicat |
| `application_id` | integer | ✗ | - |
| `old_status` | varchar(50) | ✓ | - |
| `new_status` | varchar(50) | ✗ | - |
| `changed_by` | varchar(255) | ✓ | - |
| `change_reason` | text | ✓ | - |
| `changed_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### applications 🏛️

> UI beneficiary application submissions

**Category:** `ui` | **Rows:** 5 | **Size:** 160 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.applicat |
| `application_type` | varchar(50) | ✗ | - |
| `status` | varchar(50) | ✗ | 'pending'::character vary |
| `reference_number` | varchar(50) | ✗ | - |
| `submitted_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |
| `reviewed_at` | timestamp with time zone | ✓ | - |
| `decided_at` | timestamp with time zone | ✓ | - |
| `contact_name` | varchar(255) | ✗ | - |
| `contact_email` | varchar(255) | ✗ | - |
| `contact_phone` | varchar(50) | ✓ | - |
| `location` | varchar(255) | ✗ | - |
| `organization_name` | varchar(255) | ✓ | - |
| `organization_type` | varchar(100) | ✓ | - |
| `application_data` | jsonb | ✗ | - |
| `requested_amount` | integer | ✗ | - |
| `approved_amount` | integer | ✓ | - |
| `reviewer_notes` | text | ✓ | - |
| `reviewed_by` | varchar(255) | ✓ | - |
| `decision_notes` | text | ✓ | - |
| `decided_by` | varchar(255) | ✓ | - |
| `applicant_references` | jsonb | ✓ | - |
| `agreed_terms` | boolean | ✗ | false |
| `agreed_values` | boolean | ✗ | false |
| `confirmation_sent` | boolean | ✓ | false |
| `confirmation_sent_at` | timestamp with time zone | ✓ | - |
| `created_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |
| `updated_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### contact_messages

**Category:** `other` | **Rows:** 0 | **Size:** 40 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.contact_ |
| `name` | varchar(255) | ✗ | - |
| `email` | varchar(255) | ✗ | - |
| `subject` | varchar(255) | ✓ | - |
| `message` | text | ✗ | - |
| `message_type` | varchar(50) | ✓ | 'general'::character vary |
| `status` | varchar(50) | ✓ | 'new'::character varying |
| `replied_at` | timestamp with time zone | ✓ | - |
| `replied_by` | varchar(255) | ✓ | - |
| `ip_address` | inet | ✓ | - |
| `created_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### email_log

**Category:** `email` | **Rows:** 3 | **Size:** 80 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.email_lo |
| `recipient_email` | varchar(255) | ✗ | - |
| `email_type` | varchar(100) | ✗ | - |
| `subject` | varchar(255) | ✓ | - |
| `reference_type` | varchar(50) | ✓ | - |
| `reference_id` | integer | ✓ | - |
| `status` | varchar(50) | ✓ | 'sent'::character varying |
| `error_message` | text | ✓ | - |
| `sent_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### newsletter_subscribers

**Category:** `other` | **Rows:** 0 | **Size:** 40 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.newslett |
| `email` | varchar(255) | ✗ | - |
| `name` | varchar(255) | ✓ | - |
| `is_active` | boolean | ✓ | true |
| `subscription_source` | varchar(100) | ✓ | - |
| `confirmed_at` | timestamp with time zone | ✓ | - |
| `unsubscribed_at` | timestamp with time zone | ✓ | - |
| `created_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### password_reset_tokens

**Category:** `other` | **Rows:** 0 | **Size:** 32 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.password |
| `user_id` | integer | ✗ | - |
| `token` | varchar(255) | ✗ | - |
| `expires_at` | timestamp with time zone | ✗ | - |
| `used_at` | timestamp with time zone | ✓ | - |
| `created_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### user_sessions

**Category:** `ui` | **Rows:** 0 | **Size:** 48 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.user_ses |
| `user_id` | integer | ✗ | - |
| `session_token` | varchar(255) | ✗ | - |
| `ip_address` | inet | ✓ | - |
| `user_agent` | text | ✓ | - |
| `expires_at` | timestamp with time zone | ✗ | - |
| `created_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### users

**Category:** `other` | **Rows:** 1 | **Size:** 112 kB

| Column | Type | Nullable | Default |
|--------|------|----------|--------|
| `id` | integer | ✗ | nextval('ubec_ui.users_id |
| `uuid` | uuid | ✗ | ubec_ui.uuid_generate_v4( |
| `email` | varchar(255) | ✗ | - |
| `password_hash` | varchar(255) | ✓ | - |
| `full_name` | varchar(255) | ✓ | - |
| `display_name` | varchar(100) | ✓ | - |
| `phone` | varchar(50) | ✓ | - |
| `location` | varchar(255) | ✓ | - |
| `role` | varchar(50) | ✓ | 'applicant'::character va |
| `is_active` | boolean | ✓ | true |
| `is_verified` | boolean | ✓ | false |
| `stellar_address` | varchar(56) | ✓ | - |
| `last_login_at` | timestamp with time zone | ✓ | - |
| `created_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |
| `updated_at` | timestamp with time zone | ✓ | CURRENT_TIMESTAMP |

### Relationships

| From | → | To | On Delete |
|------|---|----|-----------|
| `user_sessions.user_id` | → | `users.id` | CASCADE |
| `password_reset_tokens.user_id` | → | `users.id` | CASCADE |
| `activity_log.user_id` | → | `users.id` | SET NULL |
| `application_status_history.application_id` | → | `applications.id` | CASCADE |
| `application_documents.application_id` | → | `applications.id` | CASCADE |

---

*Generated by UBEC Protocol Schema Documenter*
*This project uses the services of Claude and Anthropic PBC.*
