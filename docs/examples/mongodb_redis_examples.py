"""
Example: Complete workflow using MongoDB and Redis integration

This example demonstrates:
1. User profile creation and caching
2. Log metadata tracking with MongoDB
3. Query caching with Redis
4. Rate limiting
5. Session management
"""

import uuid
from datetime import datetime

from app.core.redis_cache import QueryCache, RateLimiter, SessionCache
from app.logs.models_mongo import LogMetadata
from app.users.models_mongo import UserProfile
from django.contrib.auth.models import User


def example_user_workflow():
    """Complete user profile workflow"""

    # 1. Create Django user (already exists)
    django_user = User.objects.get(username="john.doe")

    # 2. Create MongoDB profile
    profile = UserProfile.create(
        user_id=django_user.id,
        tenant_id="acme-corp",
        organization="Acme Corporation",
        role="admin",
        preferences={
            "theme": "dark",
            "timezone": "America/New_York",
            "notifications": {"email": True, "browser": True, "slack": False},
        },
    )

    print(f"Created profile: {profile.to_dict()}")

    # 3. Cache user session
    session_data = {
        "user_id": django_user.id,
        "tenant_id": "acme-corp",
        "role": "admin",
        "last_activity": datetime.utcnow().isoformat(),
    }
    SessionCache.set_user_session(django_user.id, session_data, ttl=3600)

    # 4. Get profile (with caching)
    cache_key = f"user_profile:{django_user.id}"
    cached_profile = QueryCache.get(cache_key)

    if not cached_profile:
        profile = UserProfile.get_by_user_id(django_user.id)
        cached_profile = profile.to_dict()
        QueryCache.set(cache_key, cached_profile, ttl=300)
        print("Profile loaded from MongoDB")
    else:
        print("Profile loaded from cache")

    # 5. Update profile
    UserProfile.update(django_user.id, {"preferences": {"theme": "light"}})

    # Invalidate cache after update
    QueryCache.delete(cache_key)

    # 6. Track API usage
    UserProfile.increment_api_usage(django_user.id, "api_calls", 1)

    # 7. Get quota usage
    quota = UserProfile.get_quota_usage(django_user.id)
    print(f"API Quota: {quota}")

    return profile


def example_log_upload_workflow():
    """Complete log upload workflow with metadata tracking"""

    user_id = 1
    tenant_id = "acme-corp"

    # 1. Generate unique upload ID
    upload_id = (
        f"upload_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    )
    task_id = str(uuid.uuid4())

    # 2. Create log metadata entry
    metadata = LogMetadata.create(
        upload_id=upload_id,
        task_id=task_id,
        tenant_id=tenant_id,
        user_id=user_id,
        source="api-service",
        environment="production",
        service_name="web-api",
        file_name="app.log",
        file_size=1048576,
        format_type="json",
        tags=["api", "production", "web"],
    )

    print(f"Created metadata: {metadata.to_dict()}")

    # 3. Update status as processing
    LogMetadata.update_status(upload_id=upload_id, status="processing", log_count=0)

    # 4. Simulate processing (in real app, this is Celery task)
    import time

    start_time = time.time()

    # ... processing logs ...
    time.sleep(2)

    processing_time = time.time() - start_time

    # 5. Update status as success
    LogMetadata.update_status(
        upload_id=upload_id,
        status="success",
        log_count=1500,
        processing_time=processing_time,
    )

    # 6. Get updated metadata
    updated_metadata = LogMetadata.get_by_upload_id(upload_id)
    print(f"Updated metadata: {updated_metadata.to_dict()}")

    # 7. Track user upload count
    UserProfile.increment_api_usage(user_id, "logs_uploaded", 1500)

    return metadata


def example_rate_limiting():
    """Example of rate limiting implementation"""

    user_id = 1
    rate_limit_key = f"api:user:{user_id}"

    # Check if request is allowed (100 requests per hour)
    for i in range(105):
        is_allowed = RateLimiter.is_allowed(
            key=rate_limit_key, max_requests=100, window=3600
        )

        if not is_allowed:
            remaining = RateLimiter.get_remaining(rate_limit_key, 100)
            print(f"Request #{i+1}: Rate limit exceeded. Remaining: {remaining}")
            break
        else:
            print(f"Request #{i+1}: Allowed")


def example_query_caching():
    """Example of query result caching"""

    tenant_id = "acme-corp"

    # First call - cache miss
    cache_key = f"tenant_stats:{tenant_id}"
    cached_stats = QueryCache.get(cache_key)

    if not cached_stats:
        print("Cache miss - querying MongoDB")
        stats = LogMetadata.get_statistics(tenant_id, days=30)
        QueryCache.set(cache_key, stats, ttl=300)  # Cache for 5 minutes
    else:
        print("Cache hit - using cached data")
        stats = cached_stats

    print(f"Statistics: {stats}")

    # Second call - cache hit
    cached_stats = QueryCache.get(cache_key)
    if cached_stats:
        print("Second call: Cache hit!")


def example_multi_tenant_queries():
    """Example of multi-tenant data isolation"""

    tenant_id = "acme-corp"

    # 1. Get all users in tenant
    users = UserProfile.get_by_tenant(tenant_id, skip=0, limit=20)
    print(f"Found {len(users)} users in tenant {tenant_id}")

    # 2. Get log metadata with filters
    filters = {"status": "success", "environment": "production"}

    metadata_list = LogMetadata.get_by_tenant(
        tenant_id=tenant_id,
        filters=filters,
        skip=0,
        limit=10,
        sort_by="created_at",
        sort_order=-1,
    )

    print(f"Found {len(metadata_list)} successful production uploads")

    # 3. Get statistics for tenant
    stats = LogMetadata.get_statistics(tenant_id, days=7)
    print(f"7-day statistics: {stats}")

    # 4. Get recent uploads
    recent = LogMetadata.get_recent_uploads(tenant_id, limit=5)
    print(f"Recent uploads: {[m.file_name for m in recent]}")


def example_session_management():
    """Example of session caching"""

    user_id = 1

    # 1. Set session on login
    session_data = {
        "user_id": user_id,
        "tenant_id": "acme-corp",
        "role": "admin",
        "login_time": datetime.utcnow().isoformat(),
        "ip_address": "192.168.1.100",
    }

    SessionCache.set_user_session(user_id, session_data, ttl=3600)
    print("Session cached")

    # 2. Get session on subsequent requests
    cached_session = SessionCache.get_user_session(user_id)
    if cached_session:
        print(f"Session found: {cached_session}")

    # 3. Clear session on logout
    SessionCache.delete_user_session(user_id)
    print("Session cleared")

    # 4. JWT token blacklist
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    SessionCache.set_jwt_blacklist(token, ttl=3600)

    is_blacklisted = SessionCache.is_jwt_blacklisted(token)
    print(f"Token blacklisted: {is_blacklisted}")


def example_full_api_request_flow():
    """
    Complete flow of an API request with:
    - Rate limiting
    - Session validation
    - Data retrieval with caching
    - Audit logging
    """

    user_id = 1
    tenant_id = "acme-corp"

    # 1. Check rate limit
    if not RateLimiter.is_allowed(f"api:user:{user_id}", 1000, 3600):
        print("❌ Rate limit exceeded")
        return {"error": "Rate limit exceeded"}, 429

    # 2. Validate session
    session = SessionCache.get_user_session(user_id)
    if not session:
        print("❌ No active session")
        return {"error": "Unauthorized"}, 401

    # 3. Check JWT blacklist (simplified)
    token = "user_jwt_token_here"
    if SessionCache.is_jwt_blacklisted(token):
        print("❌ Token blacklisted")
        return {"error": "Token invalid"}, 401

    # 4. Get user profile with caching
    cache_key = f"user_profile:{user_id}"
    profile = QueryCache.get(cache_key)

    if not profile:
        profile_obj = UserProfile.get_by_user_id(user_id)
        profile = profile_obj.to_dict() if profile_obj else None
        if profile:
            QueryCache.set(cache_key, profile, ttl=300)

    # 5. Check tenant access
    if profile and profile["tenant_id"] != tenant_id:
        print("❌ Tenant access denied")
        return {"error": "Access denied"}, 403

    # 6. Get requested data with caching
    stats_cache_key = f"tenant_stats:{tenant_id}"
    stats = QueryCache.get(stats_cache_key)

    if not stats:
        stats = LogMetadata.get_statistics(tenant_id, days=30)
        QueryCache.set(stats_cache_key, stats, ttl=300)

    # 7. Track API usage
    UserProfile.increment_api_usage(user_id, "api_calls", 1)

    # 8. Return response
    print("✓ Request successful")
    return {"user": profile, "statistics": stats}, 200


# Run examples
if __name__ == "__main__":
    print("=" * 60)
    print("MongoDB & Redis Integration Examples")
    print("=" * 60)

    print("\n1. User Workflow Example:")
    print("-" * 60)
    # example_user_workflow()

    print("\n2. Log Upload Workflow Example:")
    print("-" * 60)
    # example_log_upload_workflow()

    print("\n3. Rate Limiting Example:")
    print("-" * 60)
    # example_rate_limiting()

    print("\n4. Query Caching Example:")
    print("-" * 60)
    # example_query_caching()

    print("\n5. Multi-Tenant Queries Example:")
    print("-" * 60)
    # example_multi_tenant_queries()

    print("\n6. Session Management Example:")
    print("-" * 60)
    # example_session_management()

    print("\n7. Full API Request Flow Example:")
    print("-" * 60)
    # result, status_code = example_full_api_request_flow()
    # print(f"Response: {result}")
    # print(f"Status: {status_code}")
