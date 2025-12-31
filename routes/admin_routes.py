"""
UBEC Protocol - Admin Routes
============================

FastAPI router for admin dashboard functionality.
Integrates with ubec_ui schema for authentication and role-based access control.

Database: ubec_ui_interface
Schema: ubec_ui

Features:
    - Database-backed authentication using ubec_ui.users
    - Role-based access control (applicant, reviewer, admin, super_admin)
    - Permission checking via ubec_ui.role_permissions
    - Audit logging for all admin actions
    - Session management with secure cookies
    - Application review and management
    - User management

Roles Hierarchy:
    - applicant: No admin access (default for new users)
    - reviewer: View applications, add review notes
    - admin: Full management except dangerous operations
    - super_admin: Complete system access including delete operations

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform
    our decisions and recommendations. This project was made possible with
    the assistance of Claude and Anthropic PBC.

Version: 2.1.0
"""

import os
import logging
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps

from fastapi import APIRouter, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Try to import bcrypt for password hashing
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logging.warning("bcrypt not available - install with: pip install bcrypt")

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

# Session configuration
SESSION_TIMEOUT_HOURS = int(os.getenv("ADMIN_SESSION_HOURS", "8"))
SESSION_COOKIE_NAME = "ubec_admin_session"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

# Security configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter(prefix="/admin", tags=["admin"])

# Templates - will be set during initialization
templates: Optional[Jinja2Templates] = None


# =============================================================================
# Admin Service (Service Registry Pattern)
# =============================================================================

class AdminService:
    """
    Admin service following the service registry pattern.
    Manages database connections, session caching, and core admin functionality.
    """
    
    SERVICE_NAME = "admin_service"
    SERVICE_VERSION = "2.1.0"
    
    def __init__(self):
        self._db_pool = None
        self._session_cache: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
        self._start_time = None
    
    async def initialize(self, db_pool) -> None:
        """Initialize the admin service with database pool."""
        self._db_pool = db_pool
        self._initialized = True
        self._start_time = datetime.utcnow()
        logger.info(f"AdminService v{self.SERVICE_VERSION} initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the admin service."""
        self._session_cache.clear()
        self._initialized = False
        logger.info("AdminService shutdown complete")
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized and self._db_pool is not None
    
    async def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        status = {
            "service": self.SERVICE_NAME,
            "version": self.SERVICE_VERSION,
            "initialized": self._initialized,
            "active_sessions": len(self._session_cache),
        }
        
        if self._start_time:
            uptime = datetime.utcnow() - self._start_time
            status["uptime_seconds"] = int(uptime.total_seconds())
        
        if self._db_pool:
            try:
                async with self._db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                    status["database"] = "connected"
            except Exception as e:
                status["database"] = f"error: {str(e)}"
        else:
            status["database"] = "not_configured"
        
        return status
    
    @property
    def db_pool(self):
        return self._db_pool
    
    @property
    def session_cache(self) -> Dict[str, Dict[str, Any]]:
        return self._session_cache


# Global service instance
_admin_service = AdminService()


async def get_admin_service() -> AdminService:
    """Get the admin service instance."""
    return _admin_service


async def initialize_admin_service(db_pool) -> None:
    """Initialize the admin service with database pool."""
    await _admin_service.initialize(db_pool)


async def shutdown_admin_service() -> None:
    """Shutdown the admin service."""
    await _admin_service.shutdown()


# =============================================================================
# Password Utilities
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    else:
        # SHA-256 fallback (less secure)
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"sha256${salt}${hashed}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    if not password or not password_hash:
        return False
    
    try:
        if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
            if BCRYPT_AVAILABLE:
                return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
            return False
        elif password_hash.startswith('sha256$'):
            parts = password_hash.split('$')
            if len(parts) == 3:
                salt, stored_hash = parts[1], parts[2]
                computed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
                return secrets.compare_digest(computed, stored_hash)
        return False
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# =============================================================================
# Session Management
# =============================================================================

def create_session(user_data: Dict[str, Any]) -> str:
    """Create a new session and return the session token."""
    session_id = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_TIMEOUT_HOURS)
    
    _admin_service.session_cache[session_id] = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "role": user_data["role"],
        "display_name": user_data.get("display_name") or user_data.get("full_name") or user_data["email"].split("@")[0],
        "permissions": user_data.get("permissions", []),
        "expires_at": expires_at,
        "created_at": datetime.utcnow()
    }
    
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session data by session ID."""
    if not session_id:
        return None
    
    session = _admin_service.session_cache.get(session_id)
    if not session:
        return None
    
    if session["expires_at"] < datetime.utcnow():
        del _admin_service.session_cache[session_id]
        return None
    
    return session


def delete_session(session_id: str) -> None:
    """Delete a session."""
    if session_id and session_id in _admin_service.session_cache:
        del _admin_service.session_cache[session_id]


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get the current authenticated user from the request."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    return get_session(session_id)


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user from database by email."""
    if not _admin_service.is_initialized():
        logger.error("Admin service not initialized")
        return None
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, uuid, email, full_name, display_name, password_hash,
                       role, is_active, is_verified, is_locked, is_admin,
                       failed_login_attempts, locked_until,
                       last_login_at, created_at
                FROM ubec_ui.users
                WHERE email = $1
            """, email.lower().strip())
            
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None


async def get_user_permissions(role: str) -> List[str]:
    """Get permissions for a role."""
    if not _admin_service.is_initialized():
        return []
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT p.name
                FROM ubec_ui.permissions p
                JOIN ubec_ui.role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role = $1
            """, role)
            
            return [row["name"] for row in rows]
    except Exception as e:
        logger.error(f"Error getting permissions: {e}")
        return []


async def update_login_success(user_id: int) -> None:
    """Update user after successful login."""
    if not _admin_service.is_initialized():
        return
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE ubec_ui.users
                SET last_login_at = CURRENT_TIMESTAMP,
                    failed_login_attempts = 0,
                    is_locked = FALSE,
                    locked_until = NULL
                WHERE id = $1
            """, user_id)
    except Exception as e:
        logger.error(f"Error updating login success: {e}")


async def update_login_failure(user_id: int) -> None:
    """Update user after failed login attempt."""
    if not _admin_service.is_initialized():
        return
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            # Increment failure count
            result = await conn.fetchrow("""
                UPDATE ubec_ui.users
                SET failed_login_attempts = COALESCE(failed_login_attempts, 0) + 1
                WHERE id = $1
                RETURNING failed_login_attempts
            """, user_id)
            
            # Lock if max attempts exceeded
            if result and result["failed_login_attempts"] >= MAX_FAILED_ATTEMPTS:
                await conn.execute("""
                    UPDATE ubec_ui.users
                    SET is_locked = TRUE,
                        locked_until = CURRENT_TIMESTAMP + INTERVAL '%s minutes'
                    WHERE id = $1
                """ % LOCKOUT_DURATION_MINUTES, user_id)
    except Exception as e:
        logger.error(f"Error updating login failure: {e}")


async def log_audit_event(
    user_id: int,
    action: str,
    resource_type: str = None,
    resource_id: int = None,
    details: Dict = None,
    ip_address: str = None
) -> None:
    """Log an admin audit event."""
    if not _admin_service.is_initialized():
        return
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            # Get user email for denormalization
            email = await conn.fetchval(
                "SELECT email FROM ubec_ui.users WHERE id = $1", user_id
            )
            
            await conn.execute("""
                INSERT INTO ubec_ui.admin_audit_log
                (user_id, user_email, action, resource_type, resource_id, details, ip_address)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, user_id, email, action, resource_type, resource_id,
                json.dumps(details) if details else None, ip_address)
    except Exception as e:
        logger.error(f"Error logging audit event: {e}")


# =============================================================================
# Permission Decorator
# =============================================================================

def require_permission(*permissions):
    """Decorator to require specific permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            if not user:
                if request.url.path.startswith("/admin/api"):
                    raise HTTPException(status_code=401, detail="Not authenticated")
                return RedirectResponse(url="/admin/login", status_code=302)
            
            # Super admin bypasses all permission checks
            if user.get("role") == "super_admin":
                request.state.user = user
                return await func(request, *args, **kwargs)
            
            # Check permissions
            user_perms = user.get("permissions", [])
            has_permission = any(p in user_perms for p in permissions)
            
            if not has_permission:
                if request.url.path.startswith("/admin/api"):
                    raise HTTPException(status_code=403, detail="Insufficient permissions")
                return HTMLResponse(
                    "<h1>403 Forbidden</h1><p>You don't have permission to access this page.</p>",
                    status_code=403
                )
            
            request.state.user = user
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Authentication Routes
# =============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None, message: str = None):
    """Render the login page."""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    if templates:
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": error,
            "message": message
        })
    
    return HTMLResponse(_get_login_html(error, message))


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission."""
    client_ip = request.client.host if request.client else None
    
    # Validate input
    if not email or not password:
        return RedirectResponse(
            url="/admin/login?error=Email+and+password+required",
            status_code=302
        )
    
    # Get user
    user = await get_user_by_email(email)
    
    if not user:
        logger.warning(f"Login attempt for non-existent user: {email}")
        return RedirectResponse(
            url="/admin/login?error=Invalid+email+or+password",
            status_code=302
        )
    
    # Check if account is locked
    if user.get("is_locked"):
        locked_until = user.get("locked_until")
        if locked_until and locked_until > datetime.utcnow():
            logger.warning(f"Login attempt for locked account: {email}")
            return RedirectResponse(
                url="/admin/login?error=Account+is+locked.+Please+try+again+later.",
                status_code=302
            )
    
    # Check if account is active
    if not user.get("is_active", True):
        logger.warning(f"Login attempt for inactive account: {email}")
        return RedirectResponse(
            url="/admin/login?error=Account+is+inactive",
            status_code=302
        )
    
    # Verify password
    if not verify_password(password, user.get("password_hash", "")):
        await update_login_failure(user["id"])
        await log_audit_event(
            user_id=user["id"], action="login_failed",
            details={"reason": "invalid_password"},
            ip_address=client_ip
        )
        return RedirectResponse(
            url="/admin/login?error=Invalid+email+or+password",
            status_code=302
        )
    
    # Check if user has admin access
    role = user.get("role", "applicant")
    if role == "applicant" and not user.get("is_admin"):
        await log_audit_event(
            user_id=user["id"], action="login_denied",
            details={"reason": "no_admin_access"},
            ip_address=client_ip
        )
        return RedirectResponse(
            url="/admin/login?error=You+do+not+have+admin+access",
            status_code=302
        )
    
    # Get permissions
    permissions = await get_user_permissions(role)
    user["permissions"] = permissions
    
    # Update login success
    await update_login_success(user["id"])
    
    # Create session
    session_id = create_session(user)
    
    # Log successful login
    await log_audit_event(
        user_id=user["id"], action="login_success",
        ip_address=client_ip
    )
    
    # Set cookie and redirect
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_TIMEOUT_HOURS * 3600
    )
    
    return response


@router.get("/logout")
async def logout(request: Request):
    """Handle logout."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    user = get_session(session_id) if session_id else None
    client_ip = request.client.host if request.client else None
    
    if user:
        await log_audit_event(
            user_id=user["user_id"], action="logout",
            ip_address=client_ip
        )
        delete_session(session_id)
    
    response = RedirectResponse(url="/admin/login?message=Logged+out+successfully", status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


# =============================================================================
# Dashboard Routes
# =============================================================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the admin dashboard."""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Get dashboard data
    stats = await get_dashboard_stats()
    pending = await get_pending_applications(limit=10)
    recent_activity = await get_recent_activity(limit=10)
    
    if templates:
        return templates.TemplateResponse("admin_dashboard.html", {
            "request": request,
            "user": user,
            "stats": stats,
            "pending_applications": pending,
            "recent_activity": recent_activity
        })
    
    return HTMLResponse(_get_dashboard_html(user, stats, pending, recent_activity))


# =============================================================================
# Application Detail Page Route
# =============================================================================

@router.get("/application/{app_id}", response_class=HTMLResponse)
@require_permission("applications.view")
async def view_application_page(request: Request, app_id: int):
    """Display single application detail page."""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            # Get application details (no user_id in applications table)
            app = await conn.fetchrow("""
                SELECT a.*
                FROM ubec_ui.applications a
                WHERE a.id = $1
            """, app_id)
            
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")
            
            # Get status history (changed_by stores email directly)
            history = await conn.fetch("""
                SELECT * FROM ubec_ui.application_status_history
                WHERE application_id = $1
                ORDER BY changed_at DESC
            """, app_id)
            
            # Get documents
            documents = await conn.fetch("""
                SELECT * FROM ubec_ui.application_documents
                WHERE application_id = $1
                ORDER BY uploaded_at DESC
            """, app_id)
        
        app_dict = dict(app)
        history_list = [dict(h) for h in history]
        docs_list = [dict(d) for d in documents]
        
        # Log the view
        client_ip = request.client.host if request.client else None
        await log_audit_event(
            user_id=user["user_id"],
            action="application_viewed",
            resource_type="application",
            resource_id=app_id,
            ip_address=client_ip
        )
        
        if templates:
            return templates.TemplateResponse("admin/application_detail.html", {
                "request": request,
                "user": user,
                "application": app_dict,
                "history": history_list,
                "documents": docs_list,
                "page_title": f"Application #{app_id}"
            })
        
        # Fallback to inline HTML
        return HTMLResponse(_get_application_detail_html(user, app_dict, history_list, docs_list))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing application {app_id}: {e}")
        raise HTTPException(status_code=500, detail="Error loading application")


@router.get("/health")
async def health_check():
    """Return service health status."""
    status = await _admin_service.health_check()
    return JSONResponse(status)


# =============================================================================
# Applications API
# =============================================================================

@router.get("/api/applications")
@require_permission("applications.view")
async def api_list_applications(
    request: Request,
    status: str = Query(None),
    limit: int = Query(50, le=200)
):
    """List applications with optional status filter."""
    try:
        async with _admin_service.db_pool.acquire() as conn:
            if status:
                rows = await conn.fetch("""
                    SELECT id, reference_number, application_type, status,
                           contact_name, contact_email, organization_name,
                           location, requested_amount, approved_amount,
                           submitted_at, reviewed_at, decided_at
                    FROM ubec_ui.applications
                    WHERE status = $1
                    ORDER BY submitted_at DESC
                    LIMIT $2
                """, status, limit)
            else:
                rows = await conn.fetch("""
                    SELECT id, reference_number, application_type, status,
                           contact_name, contact_email, organization_name,
                           location, requested_amount, approved_amount,
                           submitted_at, reviewed_at, decided_at
                    FROM ubec_ui.applications
                    ORDER BY submitted_at DESC
                    LIMIT $1
                """, limit)
            
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/api/application/{app_id}")
@require_permission("applications.view")
async def api_get_application(request: Request, app_id: int):
    """Get single application details."""
    try:
        async with _admin_service.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM ubec_ui.applications WHERE id = $1
            """, app_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Application not found")
            
            # Get documents
            docs = await conn.fetch("""
                SELECT id, document_type, filename, file_size, uploaded_at
                FROM ubec_ui.application_documents
                WHERE application_id = $1
            """, app_id)
            
            # Get status history
            history = await conn.fetch("""
                SELECT old_status, new_status, changed_by, change_reason, changed_at
                FROM ubec_ui.application_status_history
                WHERE application_id = $1
                ORDER BY changed_at DESC
            """, app_id)
            
            result = dict(row)
            result["documents"] = [dict(d) for d in docs]
            result["status_history"] = [dict(h) for h in history]
            
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application {app_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/api/application/{app_id}/review")
@require_permission("applications.review")
async def api_review_application(
    request: Request,
    app_id: int,
    notes: str = Form(...)
):
    """Add review notes to an application."""
    user = request.state.user
    client_ip = request.client.host if request.client else None
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            # Update application
            await conn.execute("""
                UPDATE ubec_ui.applications
                SET status = 'under_review',
                    reviewer_notes = COALESCE(reviewer_notes || E'\\n\\n', '') || $2,
                    reviewed_by = $3,
                    reviewed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, app_id, f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {notes}", user["email"])
            
            # Log status change
            await conn.execute("""
                INSERT INTO ubec_ui.application_status_history
                (application_id, old_status, new_status, changed_by, change_reason)
                SELECT $1, status, 'under_review', $2, $3
                FROM ubec_ui.applications WHERE id = $1
            """, app_id, user["email"], "Review notes added")
        
        await log_audit_event(
            user_id=user["user_id"], action="application_reviewed",
            resource_type="application", resource_id=app_id,
            details={"notes_length": len(notes)},
            ip_address=client_ip
        )
        
        # Redirect back to application page
        return RedirectResponse(
            url=f"/admin/application/{app_id}?message=Review+notes+added",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Error reviewing application {app_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/api/application/{app_id}/decide")
@require_permission("applications.approve")
async def api_decide_application(
    request: Request,
    app_id: int,
    decision: str = Form(...),
    notes: str = Form(None),
    approved_amount: int = Form(None)
):
    """Approve or reject an application."""
    user = request.state.user
    client_ip = request.client.host if request.client else None
    
    if decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            # Get current status
            old_status = await conn.fetchval("""
                SELECT status FROM ubec_ui.applications WHERE id = $1
            """, app_id)
            
            if not old_status:
                raise HTTPException(status_code=404, detail="Application not found")
            
            # Update application
            await conn.execute("""
                UPDATE ubec_ui.applications
                SET status = $2,
                    decision_notes = $3,
                    decided_by = $4,
                    decided_at = CURRENT_TIMESTAMP,
                    approved_amount = CASE WHEN $2 = 'approved' THEN $5 ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, app_id, decision, notes, user["email"], approved_amount)
            
            # Log status change
            await conn.execute("""
                INSERT INTO ubec_ui.application_status_history
                (application_id, old_status, new_status, changed_by, change_reason)
                VALUES ($1, $2, $3, $4, $5)
            """, app_id, old_status, decision, user["email"], notes)
        
        await log_audit_event(
            user_id=user["user_id"], action=f"application_{decision}",
            resource_type="application", resource_id=app_id,
            details={"old_status": old_status, "approved_amount": approved_amount},
            ip_address=client_ip
        )
        
        # Redirect back to application page
        return RedirectResponse(
            url=f"/admin/application/{app_id}?message=Application+{decision}",
            status_code=302
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deciding application {app_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/api/application/{app_id}/delete")
@require_permission("applications.delete")
async def api_delete_application(request: Request, app_id: int):
    """Delete an application (super_admin only)."""
    user = request.state.user
    client_ip = request.client.host if request.client else None
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            # Get application info for audit log
            app_info = await conn.fetchrow("""
                SELECT reference_number, status, contact_email
                FROM ubec_ui.applications WHERE id = $1
            """, app_id)
            
            if not app_info:
                raise HTTPException(status_code=404, detail="Application not found")
            
            # Delete related records first (cascade should handle this, but be explicit)
            await conn.execute("""
                DELETE FROM ubec_ui.application_documents WHERE application_id = $1
            """, app_id)
            
            await conn.execute("""
                DELETE FROM ubec_ui.application_status_history WHERE application_id = $1
            """, app_id)
            
            # Delete the application
            await conn.execute("""
                DELETE FROM ubec_ui.applications WHERE id = $1
            """, app_id)
        
        await log_audit_event(
            user_id=user["user_id"], action="application_deleted",
            resource_type="application", resource_id=app_id,
            details={
                "reference_number": app_info["reference_number"],
                "status": app_info["status"],
                "contact_email": app_info["contact_email"]
            },
            ip_address=client_ip
        )
        
        logger.info(f"Application {app_id} ({app_info['reference_number']}) deleted by {user['email']}")
        
        # Redirect to dashboard
        return RedirectResponse(
            url="/admin/dashboard?message=Application+deleted+successfully",
            status_code=302
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting application {app_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/api/application/{app_id}/send-email")
@require_permission("applications.review")
async def api_send_applicant_email(
    request: Request,
    app_id: int,
    subject: str = Form(...),
    message: str = Form(...)
):
    """Send an email to the applicant."""
    user = request.state.user
    client_ip = request.client.host if request.client else None
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            # Get application and contact info
            app_info = await conn.fetchrow("""
                SELECT id, reference_number, contact_name, contact_email, application_type
                FROM ubec_ui.applications WHERE id = $1
            """, app_id)
            
            if not app_info:
                raise HTTPException(status_code=404, detail="Application not found")
            
            recipient_email = app_info["contact_email"]
            recipient_name = app_info["contact_name"]
            reference_number = app_info["reference_number"]
            
            if not recipient_email:
                raise HTTPException(status_code=400, detail="No email address for this applicant")
            
            # Try to send email
            email_sent = False
            error_message = None
            
            try:
                email_sent = await send_applicant_notification(
                    to_email=recipient_email,
                    to_name=recipient_name,
                    subject=subject,
                    message_body=message,
                    reference_number=reference_number,
                    sender_name=user.get("display_name", user["email"])
                )
            except Exception as e:
                error_message = str(e)
                logger.error(f"Failed to send email to {recipient_email}: {e}")
            
            # Log the email attempt
            await conn.execute("""
                INSERT INTO ubec_ui.email_log 
                (recipient_email, email_type, subject, reference_type, reference_id, status, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                recipient_email, 
                'admin_notification',
                subject,
                'application',
                app_id,
                'sent' if email_sent else 'failed',
                error_message
            )
            
            # Add note to reviewer notes
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            email_note = f"[{timestamp}] EMAIL SENT by {user['email']}\nSubject: {subject}\nMessage: {message}"
            
            await conn.execute("""
                UPDATE ubec_ui.applications
                SET reviewer_notes = COALESCE(reviewer_notes || E'\\n\\n', '') || $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, app_id, email_note)
        
        # Audit log
        await log_audit_event(
            user_id=user["user_id"], action="applicant_email_sent",
            resource_type="application", resource_id=app_id,
            details={"recipient": recipient_email, "subject": subject, "success": email_sent},
            ip_address=client_ip
        )
        
        if email_sent:
            return RedirectResponse(
                url=f"/admin/application/{app_id}?message=Email+sent+to+{recipient_email}",
                status_code=302
            )
        else:
            return RedirectResponse(
                url=f"/admin/application/{app_id}?error=Failed+to+send+email",
                status_code=302
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email for application {app_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


async def send_applicant_notification(
    to_email: str,
    to_name: str,
    subject: str,
    message_body: str,
    reference_number: str,
    sender_name: str
) -> bool:
    """
    Send email notification to applicant.
    Uses SMTP configuration from environment variables.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Get SMTP settings from environment
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", "noreply@ubec.network")
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "UBEC Protocol")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # Build email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[{reference_number}] {subject}"
    msg['From'] = f"{smtp_from_name} <{smtp_from}>"
    msg['To'] = to_email
    msg['Reply-To'] = smtp_from
    
    # Plain text version
    text_content = f"""Dear {to_name},

{message_body}

---
Reference: {reference_number}
From: {sender_name}
UBEC Protocol - "I am because we are"

This message was sent regarding your UBEC application.
If you have questions, please reply to this email.
"""
    
    # HTML version
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
        .footer {{ background: #1f2937; color: #9ca3af; padding: 15px 20px; border-radius: 0 0 8px 8px; font-size: 0.85em; }}
        .reference {{ background: #e5e7eb; padding: 8px 12px; border-radius: 4px; font-family: monospace; display: inline-block; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin:0;">🌍 UBEC Protocol</h2>
            <p style="margin:5px 0 0 0;opacity:0.9;">"I am because we are"</p>
        </div>
        <div class="content">
            <p>Dear <strong>{to_name}</strong>,</p>
            <div style="white-space: pre-wrap;">{message_body}</div>
            <p style="margin-top: 20px;">
                <span class="reference">{reference_number}</span>
            </p>
        </div>
        <div class="footer">
            <p style="margin:0;">From: {sender_name}</p>
            <p style="margin:5px 0 0 0;">UBEC Protocol Administration</p>
        </div>
    </div>
</body>
</html>
"""
    
    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    
    # Send email
    try:
        if use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
        
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        
        server.sendmail(smtp_from, [to_email], msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"SMTP error sending to {to_email}: {e}")
        raise


# =============================================================================
# Users API
# =============================================================================

@router.get("/api/users")
@require_permission("users.view")
async def api_list_users(
    request: Request,
    role: str = Query(None),
    limit: int = Query(50, le=200)
):
    """List users with optional role filter."""
    try:
        async with _admin_service.db_pool.acquire() as conn:
            if role:
                rows = await conn.fetch("""
                    SELECT id, uuid, email, full_name, display_name, role,
                           is_active, is_verified, is_locked, is_admin,
                           last_login_at, created_at
                    FROM ubec_ui.users
                    WHERE role = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, role, limit)
            else:
                rows = await conn.fetch("""
                    SELECT id, uuid, email, full_name, display_name, role,
                           is_active, is_verified, is_locked, is_admin,
                           last_login_at, created_at
                    FROM ubec_ui.users
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
            
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.put("/api/user/{user_id}/role")
@require_permission("users.roles")
async def api_update_user_role(
    request: Request,
    user_id: int,
    role: str = Form(...)
):
    """Update a user's role."""
    current_user = request.state.user
    client_ip = request.client.host if request.client else None
    
    valid_roles = ["applicant", "reviewer", "admin", "super_admin"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be: {', '.join(valid_roles)}")
    
    # Only super_admin can create super_admins
    if role == "super_admin" and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Only super_admin can assign super_admin role")
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            old_role = await conn.fetchval("""
                SELECT role FROM ubec_ui.users WHERE id = $1
            """, user_id)
            
            if not old_role:
                raise HTTPException(status_code=404, detail="User not found")
            
            is_admin = role in ["reviewer", "admin", "super_admin"]
            await conn.execute("""
                UPDATE ubec_ui.users
                SET role = $2, is_admin = $3, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, user_id, role, is_admin)
        
        await log_audit_event(
            user_id=current_user["user_id"], action="user_role_changed",
            resource_type="user", resource_id=user_id,
            details={"old_role": old_role, "new_role": role},
            ip_address=client_ip
        )
        
        return {"success": True, "message": f"User role updated to {role}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.put("/api/user/{user_id}/lock")
@require_permission("users.lock")
async def api_toggle_user_lock(
    request: Request,
    user_id: int,
    lock: bool = Form(...)
):
    """Lock or unlock a user account."""
    current_user = request.state.user
    client_ip = request.client.host if request.client else None
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE ubec_ui.users
                SET is_locked = $2,
                    locked_until = CASE WHEN $2 THEN CURRENT_TIMESTAMP + INTERVAL '100 years' ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, user_id, lock)
        
        action = "user_locked" if lock else "user_unlocked"
        await log_audit_event(
            user_id=current_user["user_id"], action=action,
            resource_type="user", resource_id=user_id,
            ip_address=client_ip
        )
        
        return {"success": True, "message": f"User {'locked' if lock else 'unlocked'}"}
    except Exception as e:
        logger.error(f"Error toggling user lock: {e}")
        raise HTTPException(status_code=500, detail="Database error")


# =============================================================================
# Data Retrieval Helpers
# =============================================================================

async def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics."""
    if not _admin_service.is_initialized():
        return {}
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'approved') as approved,
                    COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
                    COUNT(*) FILTER (WHERE status = 'under_review') as under_review,
                    COUNT(*) as total
                FROM ubec_ui.applications
            """)
            
            users = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE role IN ('reviewer', 'admin', 'super_admin') OR is_admin) as admins
                FROM ubec_ui.users
            """)
            
            messages = await conn.fetchval("""
                SELECT COUNT(*) FROM ubec_ui.contact_messages WHERE status = 'new'
            """)
            
            return {
                "applications": dict(stats) if stats else {},
                "users": dict(users) if users else {},
                "new_messages": messages or 0
            }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {}


async def get_pending_applications(limit: int = 10) -> List[Dict[str, Any]]:
    """Get pending applications list."""
    if not _admin_service.is_initialized():
        return []
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, reference_number, application_type, contact_name,
                       contact_email, organization_name, requested_amount, submitted_at,
                       EXTRACT(DAY FROM (CURRENT_TIMESTAMP - submitted_at))::INTEGER as days_pending
                FROM ubec_ui.applications
                WHERE status = 'pending'
                ORDER BY submitted_at ASC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting pending applications: {e}")
        return []


async def get_recent_activity(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent admin activity."""
    if not _admin_service.is_initialized():
        return []
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_email, action, resource_type, resource_id, created_at
                FROM ubec_ui.admin_audit_log
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return []


# =============================================================================
# HTML Templates (Inline Fallbacks)
# =============================================================================

def _get_login_html(error: str = None, message: str = None) -> str:
    """Generate login page HTML."""
    error_html = f'<div class="alert alert-error">{error}</div>' if error else ''
    message_html = f'<div class="alert alert-success">{message}</div>' if message else ''
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UBEC Admin Login</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .login-container {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
            padding: 40px;
            width: 100%;
            max-width: 420px;
        }}
        .logo {{ text-align: center; margin-bottom: 30px; }}
        .logo h1 {{ font-size: 2em; color: #667eea; }}
        .logo p {{ color: #6c757d; font-size: 0.9em; }}
        .alert {{ padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; }}
        .alert-error {{ background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }}
        .alert-success {{ background: #d1fae5; color: #059669; border: 1px solid #a7f3d0; }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 6px; font-weight: 500; color: #374151; }}
        input {{ 
            width: 100%; 
            padding: 12px 16px; 
            border: 2px solid #e5e7eb; 
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.2s;
        }}
        input:focus {{ outline: none; border-color: #667eea; }}
        button {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        button:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }}
        .footer {{ text-align: center; margin-top: 20px; color: #9ca3af; font-size: 0.85em; }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🌍 UBEC Admin</h1>
            <p>"I am because we are"</p>
        </div>
        {error_html}
        {message_html}
        <form method="POST" action="/admin/login">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" required placeholder="admin@ubec.network">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required placeholder="••••••••">
            </div>
            <button type="submit">Sign In</button>
        </form>
        <div class="footer">
            <p>UBEC Protocol Admin Panel</p>
        </div>
    </div>
</body>
</html>"""


def _get_dashboard_html(user: Dict, stats: Dict, pending: List, activity: List) -> str:
    """Generate dashboard page HTML."""
    app_stats = stats.get("applications", {})
    user_stats = stats.get("users", {})
    
    pending_rows = ""
    for app in pending[:10]:
        pending_rows += f"""
        <tr>
            <td><strong>{app.get('reference_number', 'N/A')}</strong></td>
            <td>{app.get('application_type', 'N/A')}</td>
            <td>{app.get('contact_name', 'N/A')}</td>
            <td>{app.get('organization_name', 'N/A') or '-'}</td>
            <td>{app.get('days_pending', 0)} days</td>
            <td>
                <a href="/admin/application/{app.get('id')}" class="btn btn-sm">Review</a>
                <form method="POST" action="/admin/api/application/{app.get('id')}/delete" style="display:inline;" 
                      onsubmit="return confirm('Delete application {app.get('reference_number')}? This cannot be undone.');">
                    <button type="submit" class="btn btn-sm btn-danger">Delete</button>
                </form>
            </td>
        </tr>"""
    
    if not pending_rows:
        pending_rows = '<tr><td colspan="6" style="text-align:center;color:#6c757d;">No pending applications</td></tr>'
    
    activity_rows = ""
    for act in activity[:10]:
        created = act.get('created_at')
        time_str = created.strftime('%Y-%m-%d %H:%M') if created else 'N/A'
        activity_rows += f"""
        <tr>
            <td>{act.get('user_email', 'System')}</td>
            <td><code>{act.get('action', 'N/A')}</code></td>
            <td>{act.get('resource_type', '-') or '-'}</td>
            <td>{time_str}</td>
        </tr>"""
    
    if not activity_rows:
        activity_rows = '<tr><td colspan="4" style="text-align:center;color:#6c757d;">No recent activity</td></tr>'
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UBEC Admin Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 1.5em; }}
        .header-user {{ display: flex; align-items: center; gap: 15px; }}
        .header-user a {{ color: white; text-decoration: none; opacity: 0.9; }}
        .header-user a:hover {{ opacity: 1; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .stat-card h3 {{ color: #6c757d; font-size: 0.9em; font-weight: 500; margin-bottom: 8px; }}
        .stat-card .value {{ font-size: 2.5em; font-weight: 700; color: #1f2937; }}
        .stat-card.pending .value {{ color: #f59e0b; }}
        .stat-card.approved .value {{ color: #10b981; }}
        .card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
        .card h2 {{ margin-bottom: 20px; color: #1f2937; font-size: 1.25em; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; color: #6b7280; font-size: 0.85em; text-transform: uppercase; }}
        tr:hover {{ background: #f9fafb; }}
        .btn {{ 
            padding: 6px 12px; 
            background: #667eea; 
            color: white; 
            border-radius: 6px; 
            text-decoration: none;
            font-size: 0.85em;
            border: none;
            cursor: pointer;
        }}
        .btn:hover {{ background: #5a6fd6; }}
        .btn-danger {{ background: #ef4444; }}
        .btn-danger:hover {{ background: #dc2626; }}
        code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }}
        .role-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .role-super_admin {{ background: #fef3c7; color: #92400e; }}
        .role-admin {{ background: #dbeafe; color: #1e40af; }}
        .role-reviewer {{ background: #d1fae5; color: #065f46; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌍 UBEC Admin Dashboard</h1>
        <div class="header-user">
            <span>{user.get('display_name', 'Admin')}</span>
            <span class="role-badge role-{user.get('role', 'user')}">{user.get('role', 'user')}</span>
            <a href="/admin/logout">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card pending">
                <h3>Pending Applications</h3>
                <div class="value">{app_stats.get('pending', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Under Review</h3>
                <div class="value">{app_stats.get('under_review', 0)}</div>
            </div>
            <div class="stat-card approved">
                <h3>Approved</h3>
                <div class="value">{app_stats.get('approved', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Total Applications</h3>
                <div class="value">{app_stats.get('total', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Total Users</h3>
                <div class="value">{user_stats.get('total', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>New Messages</h3>
                <div class="value">{stats.get('new_messages', 0)}</div>
            </div>
        </div>
        
        <div class="card">
            <h2>📋 Pending Applications</h2>
            <table>
                <thead>
                    <tr>
                        <th>Reference</th>
                        <th>Type</th>
                        <th>Contact</th>
                        <th>Organization</th>
                        <th>Age</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {pending_rows}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>📝 Recent Activity</h2>
            <table>
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Action</th>
                        <th>Resource</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
                    {activity_rows}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""


def _get_application_detail_html(user: Dict, app: Dict, history: List, documents: List) -> str:
    """Generate application detail page HTML."""
    
    # Format dates
    submitted = app.get('submitted_at')
    submitted_str = submitted.strftime('%Y-%m-%d %H:%M') if submitted else 'N/A'
    
    reviewed = app.get('reviewed_at')
    reviewed_str = reviewed.strftime('%Y-%m-%d %H:%M') if reviewed else 'Not yet reviewed'
    
    decided = app.get('decided_at')
    decided_str = decided.strftime('%Y-%m-%d %H:%M') if decided else 'Pending'
    
    # Status badge color
    status = app.get('status', 'pending')
    status_colors = {
        'pending': '#f59e0b',
        'under_review': '#3b82f6',
        'approved': '#10b981',
        'rejected': '#ef4444'
    }
    status_color = status_colors.get(status, '#6b7280')
    
    # Build history rows
    history_rows = ""
    for h in history:
        changed_at = h.get('changed_at')
        time_str = changed_at.strftime('%Y-%m-%d %H:%M') if changed_at else 'N/A'
        old_color = status_colors.get(h.get('old_status'), '#6b7280')
        new_color = status_colors.get(h.get('new_status'), '#6b7280')
        history_rows += f"""
        <tr>
            <td><span class="status-badge" style="background:{old_color}20;color:{old_color}">{h.get('old_status', 'N/A')}</span></td>
            <td>→</td>
            <td><span class="status-badge" style="background:{new_color}20;color:{new_color}">{h.get('new_status', 'N/A')}</span></td>
            <td>{h.get('changed_by', 'System')}</td>
            <td>{h.get('change_reason') or '-'}</td>
            <td>{time_str}</td>
        </tr>"""
    
    if not history_rows:
        history_rows = '<tr><td colspan="6" style="text-align:center;color:#6c757d;">No status changes recorded</td></tr>'
    
    # Build documents rows
    docs_rows = ""
    for d in documents:
        uploaded = d.get('uploaded_at')
        time_str = uploaded.strftime('%Y-%m-%d %H:%M') if uploaded else 'N/A'
        size = d.get('file_size', 0)
        size_str = f"{size / 1024:.1f} KB" if size else 'N/A'
        docs_rows += f"""
        <tr>
            <td>{d.get('document_type', 'Document')}</td>
            <td>{d.get('filename', 'N/A')}</td>
            <td>{size_str}</td>
            <td>{time_str}</td>
        </tr>"""
    
    if not docs_rows:
        docs_rows = '<tr><td colspan="4" style="text-align:center;color:#6c757d;">No documents uploaded</td></tr>'
    
    requested_amount = app.get('requested_amount') or 0
    approved_amount = app.get('approved_amount') or 0
    
    # Build the page
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Application #{app.get('id')} - UBEC Admin</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 1.5em; }}
        .header-nav {{ display: flex; align-items: center; gap: 20px; }}
        .header-nav a {{ color: white; text-decoration: none; opacity: 0.9; }}
        .header-nav a:hover {{ opacity: 1; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px; }}
        .breadcrumb {{ margin-bottom: 20px; color: #6b7280; }}
        .breadcrumb a {{ color: #667eea; text-decoration: none; }}
        .breadcrumb a:hover {{ text-decoration: underline; }}
        .page-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
        .page-header h2 {{ font-size: 1.75em; color: #1f2937; }}
        .status-badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
        .card h3 {{ margin-bottom: 20px; color: #1f2937; font-size: 1.1em; border-bottom: 1px solid #e5e7eb; padding-bottom: 10px; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .info-item label {{ display: block; font-size: 0.8em; color: #6b7280; text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }}
        .info-item .value {{ font-size: 1em; color: #1f2937; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; color: #6b7280; font-size: 0.85em; text-transform: uppercase; }}
        tr:hover {{ background: #f9fafb; }}
        .notes-box {{ background: #f9fafb; border-radius: 8px; padding: 16px; white-space: pre-wrap; font-family: inherit; line-height: 1.6; }}
        .btn {{
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .btn-primary {{ background: #667eea; color: white; }}
        .btn-primary:hover {{ background: #5a6fd6; }}
        .btn-success {{ background: #10b981; color: white; }}
        .btn-success:hover {{ background: #059669; }}
        .btn-danger {{ background: #ef4444; color: white; }}
        .btn-danger:hover {{ background: #dc2626; }}
        .btn-secondary {{ background: #e5e7eb; color: #374151; }}
        .btn-secondary:hover {{ background: #d1d5db; }}
        textarea {{ width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1em; font-family: inherit; resize: vertical; min-height: 100px; }}
        textarea:focus {{ outline: none; border-color: #667eea; }}
        .form-group {{ margin-bottom: 16px; }}
        .form-group label {{ display: block; margin-bottom: 6px; font-weight: 500; color: #374151; }}
        input[type="number"] {{ width: 200px; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1em; }}
        input[type="number"]:focus {{ outline: none; border-color: #667eea; }}
        input[type="text"] {{ padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1em; }}
        input[type="text"]:focus {{ outline: none; border-color: #667eea; }}
        .action-buttons {{ display: flex; gap: 12px; margin-top: 20px; }}
        .role-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .role-super_admin {{ background: #fef3c7; color: #92400e; }}
        .role-admin {{ background: #dbeafe; color: #1e40af; }}
        .role-reviewer {{ background: #d1fae5; color: #065f46; }}
        hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌍 UBEC Admin</h1>
        <div class="header-nav">
            <a href="/admin/dashboard">Dashboard</a>
            <span>{user.get('display_name', 'Admin')}</span>
            <span class="role-badge role-{user.get('role', 'user')}">{user.get('role', 'user')}</span>
            <a href="/admin/logout">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="breadcrumb">
            <a href="/admin/dashboard">Dashboard</a> / Application #{app.get('id')}
        </div>
        
        <div class="page-header">
            <h2>Application: {app.get('reference_number', 'N/A')}</h2>
            <span class="status-badge" style="background:{status_color}20;color:{status_color}">{status}</span>
        </div>
        
        <!-- Application Info -->
        <div class="card">
            <h3>📋 Application Information</h3>
            <div class="info-grid">
                <div class="info-item">
                    <label>Reference Number</label>
                    <div class="value">{app.get('reference_number', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <label>Application Type</label>
                    <div class="value">{app.get('application_type', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <label>Submitted</label>
                    <div class="value">{submitted_str}</div>
                </div>
                <div class="info-item">
                    <label>Status</label>
                    <div class="value"><span class="status-badge" style="background:{status_color}20;color:{status_color}">{status}</span></div>
                </div>
            </div>
        </div>
        
        <!-- Contact Info -->
        <div class="card">
            <h3>👤 Contact Information</h3>
            <div class="info-grid">
                <div class="info-item">
                    <label>Contact Name</label>
                    <div class="value">{app.get('contact_name', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <label>Email</label>
                    <div class="value">{app.get('contact_email', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <label>Phone</label>
                    <div class="value">{app.get('contact_phone') or 'N/A'}</div>
                </div>
                <div class="info-item">
                    <label>Organization</label>
                    <div class="value">{app.get('organization_name') or 'N/A'}</div>
                </div>
                <div class="info-item">
                    <label>Location</label>
                    <div class="value">{app.get('location') or 'N/A'}</div>
                </div>
                <div class="info-item">
                    <label>Bioregion</label>
                    <div class="value">{app.get('bioregion') or 'N/A'}</div>
                </div>
            </div>
        </div>
        
        <!-- Financial Info -->
        <div class="card">
            <h3>💰 Financial Information</h3>
            <div class="info-grid">
                <div class="info-item">
                    <label>Requested Amount</label>
                    <div class="value">{requested_amount:,} UBEC</div>
                </div>
                <div class="info-item">
                    <label>Approved Amount</label>
                    <div class="value">{approved_amount:,} UBEC</div>
                </div>
                <div class="info-item">
                    <label>Reviewed At</label>
                    <div class="value">{reviewed_str}</div>
                </div>
                <div class="info-item">
                    <label>Decided At</label>
                    <div class="value">{decided_str}</div>
                </div>
            </div>
        </div>
        
        <!-- Description -->
        <div class="card">
            <h3>📝 Description</h3>
            <div class="notes-box">{app.get('description') or 'No description provided.'}</div>
        </div>
        
        <!-- Reviewer Notes -->
        <div class="card">
            <h3>📋 Reviewer Notes</h3>
            <div class="notes-box">{app.get('reviewer_notes') or 'No reviewer notes yet.'}</div>
        </div>
        
        <!-- Documents -->
        <div class="card">
            <h3>📎 Documents</h3>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Filename</th>
                        <th>Size</th>
                        <th>Uploaded</th>
                    </tr>
                </thead>
                <tbody>
                    {docs_rows}
                </tbody>
            </table>
        </div>
        
        <!-- Status History -->
        <div class="card">
            <h3>📊 Status History</h3>
            <table>
                <thead>
                    <tr>
                        <th>From</th>
                        <th></th>
                        <th>To</th>
                        <th>Changed By</th>
                        <th>Reason</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
                    {history_rows}
                </tbody>
            </table>
        </div>
        
        <!-- Contact Applicant -->
        <div class="card">
            <h3>✉️ Contact Applicant</h3>
            <p style="color: #6b7280; margin-bottom: 15px;">Send an email to <strong>{app.get('contact_name', 'Applicant')}</strong> ({app.get('contact_email', 'N/A')})</p>
            <form method="POST" action="/admin/api/application/{app.get('id')}/send-email">
                <div class="form-group">
                    <label for="email_subject">Subject</label>
                    <input type="text" id="email_subject" name="subject" 
                           placeholder="Re: Your UBEC Application" 
                           value="Regarding your {app.get('application_type', '')} application"
                           style="width: 100%; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1em;"
                           required>
                </div>
                <div class="form-group">
                    <label for="email_message">Message</label>
                    <textarea id="email_message" name="message" 
                              placeholder="Enter your message to the applicant..." 
                              style="min-height: 150px;" required></textarea>
                </div>
                <button type="submit" class="btn btn-primary">📧 Send Email</button>
            </form>
        </div>
        
        <!-- Review Actions -->
        <div class="card">
            <h3>⚡ Actions</h3>
            
            <form method="POST" action="/admin/api/application/{app.get('id')}/review" style="margin-bottom: 20px;">
                <div class="form-group">
                    <label for="notes">Add Review Notes</label>
                    <textarea id="notes" name="notes" placeholder="Enter your review notes..." required></textarea>
                </div>
                <button type="submit" class="btn btn-primary">💬 Add Notes</button>
            </form>
            
            <hr>
            
            <form method="POST" action="/admin/api/application/{app.get('id')}/decide">
                <div class="form-group">
                    <label for="approved_amount">Approved Amount (UBEC)</label>
                    <input type="number" id="approved_amount" name="approved_amount" value="{requested_amount}" min="0">
                </div>
                <div class="form-group">
                    <label for="decision_notes">Decision Notes</label>
                    <textarea id="decision_notes" name="notes" placeholder="Enter decision notes..."></textarea>
                </div>
                <div class="action-buttons">
                    <button type="submit" name="decision" value="approved" class="btn btn-success">✅ Approve</button>
                    <button type="submit" name="decision" value="rejected" class="btn btn-danger">❌ Reject</button>
                    <a href="/admin/dashboard" class="btn btn-secondary">← Back to Dashboard</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>"""


# =============================================================================
# Module Initialization
# =============================================================================

def init_templates(templates_instance: Jinja2Templates) -> None:
    """Initialize templates for the admin module."""
    global templates
    templates = templates_instance
    logger.info("Admin templates initialized")
