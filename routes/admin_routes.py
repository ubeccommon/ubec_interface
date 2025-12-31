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

Version: 2.0.0
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
    SERVICE_VERSION = "2.0.0"
    
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
        "display_name": user_data.get("display_name") or user_data.get("full_name", "User"),
        "permissions": user_data.get("permissions", []),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat()
    }
    
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session data if valid and not expired."""
    if not session_id or session_id not in _admin_service.session_cache:
        return None
    
    session = _admin_service.session_cache[session_id]
    expires_at = datetime.fromisoformat(session["expires_at"])
    
    if datetime.utcnow() > expires_at:
        del _admin_service.session_cache[session_id]
        return None
    
    return session


def delete_session(session_id: str) -> None:
    """Delete a session."""
    if session_id in _admin_service.session_cache:
        del _admin_service.session_cache[session_id]


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from session cookie."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    return get_session(session_id) if session_id else None


# =============================================================================
# Database Operations
# =============================================================================

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from database."""
    if not _admin_service.is_initialized():
        logger.error("Admin service not initialized")
        return None
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, uuid, email, password_hash, full_name, display_name,
                       role, is_active, is_verified, is_locked, is_admin,
                       failed_login_attempts, locked_until, last_login_at
                FROM ubec_ui.users
                WHERE LOWER(email) = LOWER($1)
            """, email)
            
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
        return None


async def get_user_permissions(role: str) -> List[str]:
    """Get all permissions for a role."""
    if not _admin_service.is_initialized():
        return []
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT p.name
                FROM ubec_ui.permissions p
                JOIN ubec_ui.role_permissions rp ON rp.permission_id = p.id
                WHERE rp.role = $1
            """, role)
            
            return [row['name'] for row in rows]
    except Exception as e:
        logger.error(f"Error fetching permissions for role {role}: {e}")
        return []


async def update_login_success(user_id: int) -> None:
    """Update user record on successful login."""
    if not _admin_service.is_initialized():
        return
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE ubec_ui.users
                SET failed_login_attempts = 0,
                    is_locked = FALSE,
                    locked_until = NULL,
                    last_login_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, user_id)
    except Exception as e:
        logger.error(f"Error updating login success: {e}")


async def update_login_failure(user_id: int) -> None:
    """Update user record on failed login."""
    if not _admin_service.is_initialized():
        return
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            current = await conn.fetchval("""
                SELECT COALESCE(failed_login_attempts, 0) 
                FROM ubec_ui.users WHERE id = $1
            """, user_id)
            
            new_attempts = (current or 0) + 1
            
            if new_attempts >= MAX_FAILED_ATTEMPTS:
                locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                await conn.execute("""
                    UPDATE ubec_ui.users
                    SET failed_login_attempts = $2,
                        is_locked = TRUE,
                        locked_until = $3,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, user_id, new_attempts, locked_until)
            else:
                await conn.execute("""
                    UPDATE ubec_ui.users
                    SET failed_login_attempts = $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, user_id, new_attempts)
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
    """Log an admin action to the audit log."""
    if not _admin_service.is_initialized():
        return
    
    try:
        async with _admin_service.db_pool.acquire() as conn:
            user_email = await conn.fetchval("""
                SELECT email FROM ubec_ui.users WHERE id = $1
            """, user_id) if user_id else None
            
            details_json = json.dumps(details) if details else None
            
            await conn.execute("""
                INSERT INTO ubec_ui.admin_audit_log 
                (user_id, user_email, action, resource_type, resource_id, details, ip_address)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::inet)
            """, user_id, user_email, action, resource_type, resource_id, 
                details_json, ip_address)
    except Exception as e:
        logger.error(f"Error logging audit event: {e}")


# =============================================================================
# Authentication Decorators
# =============================================================================

def require_permission(*permissions):
    """Decorator to require specific permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            
            if not user:
                if request.url.path.startswith("/admin/api/"):
                    raise HTTPException(status_code=401, detail="Not authenticated")
                return RedirectResponse(url="/admin/login", status_code=302)
            
            user_perms = user.get("permissions", [])
            if permissions and not any(p in user_perms for p in permissions):
                if request.url.path.startswith("/admin/api/"):
                    raise HTTPException(status_code=403, detail="Permission denied")
                raise HTTPException(status_code=403, detail="You don't have permission to access this resource")
            
            request.state.user = user
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Login Routes
# =============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None, message: str = None):
    """Render the admin login page."""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    if templates:
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": error,
            "message": message
        })
    
    # Inline login template
    return HTMLResponse(_get_login_html(error, message))


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission."""
    client_ip = request.client.host if request.client else None
    
    # Get user from database
    user = await get_user_by_email(email)
    
    if not user:
        await log_audit_event(
            user_id=0, action="login_failed",
            details={"reason": "user_not_found", "email": email},
            ip_address=client_ip
        )
        return RedirectResponse(
            url="/admin/login?error=Invalid+email+or+password",
            status_code=302
        )
    
    # Check account status
    if not user.get("is_active"):
        await log_audit_event(
            user_id=user["id"], action="login_failed",
            details={"reason": "account_inactive"},
            ip_address=client_ip
        )
        return RedirectResponse(
            url="/admin/login?error=Account+is+inactive",
            status_code=302
        )
    
    # Check lockout
    if user.get("is_locked"):
        locked_until = user.get("locked_until")
        if locked_until and datetime.utcnow() < locked_until.replace(tzinfo=None):
            await log_audit_event(
                user_id=user["id"], action="login_failed",
                details={"reason": "account_locked"},
                ip_address=client_ip
            )
            return RedirectResponse(
                url="/admin/login?error=Account+is+temporarily+locked.+Try+again+later.",
                status_code=302
            )
    
    # Check admin access
    if user.get("role") == "applicant" and not user.get("is_admin"):
        await log_audit_event(
            user_id=user["id"], action="login_failed",
            details={"reason": "no_admin_access"},
            ip_address=client_ip
        )
        return RedirectResponse(
            url="/admin/login?error=You+do+not+have+admin+access",
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
    
    # Successful login
    await update_login_success(user["id"])
    
    # Get permissions
    permissions = await get_user_permissions(user["role"])
    user["permissions"] = permissions
    
    # Create session
    session_id = create_session(user)
    
    await log_audit_event(
        user_id=user["id"], action="login_success",
        details={"role": user["role"], "permissions_count": len(permissions)},
        ip_address=client_ip
    )
    
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
                    reviewer_notes = COALESCE(reviewer_notes || E'\n\n', '') || $2,
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
        
        return {"success": True, "message": "Review notes added"}
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
        
        return {"success": True, "message": f"Application {decision}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deciding application {app_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


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
        }}
        .btn:hover {{ background: #5a6fd6; }}
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


# =============================================================================
# Module Initialization
# =============================================================================

def init_templates(templates_instance: Jinja2Templates) -> None:
    """Initialize templates for the admin module."""
    global templates
    templates = templates_instance
    logger.info("Admin templates initialized")
