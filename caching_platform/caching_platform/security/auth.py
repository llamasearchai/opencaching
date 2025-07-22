"""Authentication and authorization for the caching platform."""

import jwt
import hashlib
import secrets
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog

from ..config.settings import get_settings

logger = structlog.get_logger(__name__)


class AuthenticationManager:
    """Authentication and authorization manager."""
    
    def __init__(self):
        self.settings = get_settings()
        self.security_config = self.settings.security
        
        # User management
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        
        # Rate limiting
        self.rate_limiters: Dict[str, Dict[str, Any]] = {}
        
        # Audit logging
        self.audit_log: List[Dict[str, Any]] = []
        
        # Initialize default admin user
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Initialize default users."""
        try:
            # Create default admin user
            admin_password = self._hash_password("admin123")
            self.users["admin"] = {
                "id": "admin",
                "username": "admin",
                "email": "admin@cachingplatform.com",
                "password_hash": admin_password,
                "role": "admin",
                "permissions": ["*"],  # All permissions
                "created_at": datetime.utcnow(),
                "last_login": None,
                "active": True
            }
            
            logger.info("Initialized default admin user")
            
        except Exception as e:
            logger.error("Failed to initialize default users", error=str(e))
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self, user_id: str, expires_in: int = None) -> str:
        """Generate a JWT token for a user."""
        try:
            if expires_in is None:
                expires_in = self.security_config.jwt_expiry_hours * 3600
            
            payload = {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(seconds=expires_in),
                "iat": datetime.utcnow(),
                "iss": "caching-platform"
            }
            
            token = jwt.encode(payload, self.security_config.jwt_secret, algorithm="HS256")
            return token
            
        except Exception as e:
            logger.error("Error generating token", error=str(e))
            return None
    
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token."""
        try:
            payload = jwt.decode(token, self.security_config.jwt_secret, algorithms=["HS256"])
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error("Error verifying token", error=str(e))
            return None
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)
    
    def _check_rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """Check if a request is within rate limits."""
        try:
            current_time = time.time()
            
            if identifier not in self.rate_limiters:
                self.rate_limiters[identifier] = {
                    "requests": [],
                    "limit": limit,
                    "window": window
                }
            
            rate_limiter = self.rate_limiters[identifier]
            
            # Remove old requests outside the window
            rate_limiter["requests"] = [
                req_time for req_time in rate_limiter["requests"]
                if current_time - req_time < window
            ]
            
            # Check if under limit
            if len(rate_limiter["requests"]) < limit:
                rate_limiter["requests"].append(current_time)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error checking rate limit", error=str(e))
            return False
    
    def _log_audit_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log an audit event."""
        try:
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "details": details,
                "ip_address": details.get("ip_address", "unknown"),
                "user_agent": details.get("user_agent", "unknown")
            }
            
            self.audit_log.append(audit_entry)
            
            # Keep only last 10000 entries
            if len(self.audit_log) > 10000:
                self.audit_log.pop(0)
            
        except Exception as e:
            logger.error("Error logging audit event", error=str(e))
    
    async def authenticate_user(self, username: str, password: str, 
                              ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password."""
        try:
            # Check if user exists
            if username not in self.users:
                self._log_audit_event("login_failed", username, {
                    "reason": "user_not_found",
                    "ip_address": ip_address,
                    "user_agent": user_agent
                })
                return None
            
            user = self.users[username]
            
            # Check if user is active
            if not user["active"]:
                self._log_audit_event("login_failed", username, {
                    "reason": "account_disabled",
                    "ip_address": ip_address,
                    "user_agent": user_agent
                })
                return None
            
            # Verify password
            password_hash = self._hash_password(password)
            if password_hash != user["password_hash"]:
                self._log_audit_event("login_failed", username, {
                    "reason": "invalid_password",
                    "ip_address": ip_address,
                    "user_agent": user_agent
                })
                return None
            
            # Check rate limiting
            rate_limit_key = f"login:{ip_address}"
            if not self._check_rate_limit(rate_limit_key, 5, 300):  # 5 attempts per 5 minutes
                self._log_audit_event("login_failed", username, {
                    "reason": "rate_limit_exceeded",
                    "ip_address": ip_address,
                    "user_agent": user_agent
                })
                return None
            
            # Generate token
            token = self._generate_token(user["id"])
            if not token:
                return None
            
            # Update last login
            user["last_login"] = datetime.utcnow()
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = {
                "user_id": user["id"],
                "token": token,
                "created_at": datetime.utcnow(),
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            # Log successful login
            self._log_audit_event("login_success", username, {
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_id": session_id
            })
            
            return {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "permissions": user["permissions"],
                "token": token,
                "session_id": session_id,
                "expires_in": self.security_config.jwt_expiry_hours * 3600
            }
            
        except Exception as e:
            logger.error("Error authenticating user", error=str(e))
            return None
    
    async def authenticate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with a JWT token."""
        try:
            # Verify token
            payload = self._verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("user_id")
            if user_id not in self.users:
                return None
            
            user = self.users[user_id]
            if not user["active"]:
                return None
            
            return {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "permissions": user["permissions"]
            }
            
        except Exception as e:
            logger.error("Error authenticating token", error=str(e))
            return None
    
    async def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with an API key."""
        try:
            if api_key not in self.api_keys:
                return None
            
            key_info = self.api_keys[api_key]
            
            # Check if key is active
            if not key_info["active"]:
                return None
            
            # Check if key is expired
            if key_info["expires_at"] and datetime.utcnow() > key_info["expires_at"]:
                return None
            
            # Get user info
            user_id = key_info["user_id"]
            if user_id not in self.users:
                return None
            
            user = self.users[user_id]
            if not user["active"]:
                return None
            
            return {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "permissions": user["permissions"],
                "api_key_id": key_info["id"]
            }
            
        except Exception as e:
            logger.error("Error authenticating API key", error=str(e))
            return None
    
    async def check_permission(self, user: Dict[str, Any], permission: str) -> bool:
        """Check if a user has a specific permission."""
        try:
            if not user:
                return False
            
            permissions = user.get("permissions", [])
            
            # Admin role has all permissions
            if user.get("role") == "admin":
                return True
            
            # Check specific permission
            if permission in permissions:
                return True
            
            # Check wildcard permissions
            for perm in permissions:
                if perm.endswith("*") and permission.startswith(perm[:-1]):
                    return True
            
            return False
            
        except Exception as e:
            logger.error("Error checking permission", error=str(e))
            return False
    
    async def create_user(self, username: str, email: str, password: str, 
                         role: str = "user", permissions: List[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new user."""
        try:
            if username in self.users:
                logger.warning(f"User {username} already exists")
                return None
            
            if permissions is None:
                permissions = []
            
            user = {
                "id": username,
                "username": username,
                "email": email,
                "password_hash": self._hash_password(password),
                "role": role,
                "permissions": permissions,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "active": True
            }
            
            self.users[username] = user
            
            logger.info(f"Created user {username}")
            return user
            
        except Exception as e:
            logger.error("Error creating user", error=str(e))
            return None
    
    async def update_user(self, username: str, updates: Dict[str, Any]) -> bool:
        """Update a user."""
        try:
            if username not in self.users:
                return False
            
            user = self.users[username]
            
            # Update allowed fields
            allowed_fields = ["email", "role", "permissions", "active"]
            for field, value in updates.items():
                if field in allowed_fields:
                    user[field] = value
            
            logger.info(f"Updated user {username}")
            return True
            
        except Exception as e:
            logger.error("Error updating user", error=str(e))
            return False
    
    async def delete_user(self, username: str) -> bool:
        """Delete a user."""
        try:
            if username not in self.users:
                return False
            
            # Remove user's API keys
            keys_to_remove = []
            for key, key_info in self.api_keys.items():
                if key_info["user_id"] == username:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.api_keys[key]
            
            # Remove user's sessions
            sessions_to_remove = []
            for session_id, session in self.sessions.items():
                if session["user_id"] == username:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
            
            # Remove user
            del self.users[username]
            
            logger.info(f"Deleted user {username}")
            return True
            
        except Exception as e:
            logger.error("Error deleting user", error=str(e))
            return False
    
    async def create_api_key(self, user_id: str, name: str, 
                           expires_in_days: int = None) -> Optional[Dict[str, Any]]:
        """Create an API key for a user."""
        try:
            if user_id not in self.users:
                return None
            
            api_key = self._generate_api_key()
            key_id = f"key_{int(time.time())}"
            
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            key_info = {
                "id": key_id,
                "user_id": user_id,
                "name": name,
                "key_hash": self._hash_password(api_key),
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "active": True,
                "last_used": None
            }
            
            self.api_keys[api_key] = key_info
            
            logger.info(f"Created API key {key_id} for user {user_id}")
            return {
                "key_id": key_id,
                "api_key": api_key,
                "name": name,
                "expires_at": expires_at
            }
            
        except Exception as e:
            logger.error("Error creating API key", error=str(e))
            return None
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        try:
            for api_key, key_info in self.api_keys.items():
                if key_info["id"] == key_id:
                    key_info["active"] = False
                    logger.info(f"Revoked API key {key_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error("Error revoking API key", error=str(e))
            return False
    
    async def logout(self, session_id: str) -> bool:
        """Logout a user by invalidating their session."""
        try:
            if session_id in self.sessions:
                user_id = self.sessions[session_id]["user_id"]
                del self.sessions[session_id]
                
                self._log_audit_event("logout", user_id, {
                    "session_id": session_id
                })
                
                logger.info(f"User {user_id} logged out")
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error logging out", error=str(e))
            return False
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users (without sensitive information)."""
        try:
            users = []
            for user in self.users.values():
                users.append({
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "permissions": user["permissions"],
                    "created_at": user["created_at"],
                    "last_login": user["last_login"],
                    "active": user["active"]
                })
            
            return users
            
        except Exception as e:
            logger.error("Error getting users", error=str(e))
            return []
    
    async def get_api_keys(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get API keys for a user or all API keys."""
        try:
            keys = []
            for api_key, key_info in self.api_keys.items():
                if user_id is None or key_info["user_id"] == user_id:
                    keys.append({
                        "id": key_info["id"],
                        "name": key_info["name"],
                        "user_id": key_info["user_id"],
                        "created_at": key_info["created_at"],
                        "expires_at": key_info["expires_at"],
                        "active": key_info["active"],
                        "last_used": key_info["last_used"]
                    })
            
            return keys
            
        except Exception as e:
            logger.error("Error getting API keys", error=str(e))
            return []
    
    async def get_audit_log(self, user_id: str = None, event_type: str = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries with optional filtering."""
        try:
            filtered_log = self.audit_log
            
            if user_id:
                filtered_log = [entry for entry in filtered_log if entry["user_id"] == user_id]
            
            if event_type:
                filtered_log = [entry for entry in filtered_log if entry["event_type"] == event_type]
            
            # Sort by timestamp (newest first)
            filtered_log.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return filtered_log[:limit]
            
        except Exception as e:
            logger.error("Error getting audit log", error=str(e))
            return []
    
    async def check_rate_limit(self, identifier: str, limit: int = None, window: int = None) -> bool:
        """Check rate limiting for a specific identifier."""
        try:
            if limit is None:
                limit = self.security_config.max_requests_per_minute
            
            if window is None:
                window = 60  # 1 minute
            
            return self._check_rate_limit(identifier, limit, window)
            
        except Exception as e:
            logger.error("Error checking rate limit", error=str(e))
            return False 