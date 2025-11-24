"""
MongoDB models/schemas for user profiles
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.core.mongodb import get_collection, COLLECTION_USER_PROFILES


class UserProfile:
    """
    User Profile model stored in MongoDB
    Extends Django User model with additional metadata
    """
    
    def __init__(self, data: dict):
        self._id = data.get('_id')
        self.user_id = data.get('user_id')  # Django User ID
        self.tenant_id = data.get('tenant_id')
        self.organization = data.get('organization')
        self.role = data.get('role', 'viewer')
        self.preferences = data.get('preferences', {})
        self.api_quota = data.get('api_quota', {})
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self.last_login = data.get('last_login')
        self.metadata = data.get('metadata', {})
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            '_id': str(self._id) if self._id else None,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'organization': self.organization,
            'role': self.role,
            'preferences': self.preferences,
            'api_quota': self.api_quota,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            'metadata': self.metadata
        }
    
    @staticmethod
    def create(user_id: int, tenant_id: str, **kwargs) -> 'UserProfile':
        """
        Create new user profile
        
        Args:
            user_id: Django user ID
            tenant_id: Tenant identifier
            **kwargs: Additional profile data
            
        Returns:
            UserProfile: Created profile
        """
        collection = get_collection(COLLECTION_USER_PROFILES)
        
        now = datetime.utcnow()
        profile_data = {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'organization': kwargs.get('organization'),
            'role': kwargs.get('role', 'viewer'),
            'preferences': kwargs.get('preferences', {
                'theme': 'light',
                'timezone': 'UTC',
                'notifications': {
                    'email': True,
                    'browser': True,
                    'slack': False
                },
                'default_dashboard': None
            }),
            'api_quota': kwargs.get('api_quota', {
                'logs_per_day': 100000,
                'api_calls_per_hour': 1000,
                'retention_days': 90
            }),
            'created_at': now,
            'updated_at': now,
            'last_login': None,
            'metadata': kwargs.get('metadata', {})
        }
        
        result = collection.insert_one(profile_data)
        profile_data['_id'] = result.inserted_id
        
        return UserProfile(profile_data)
    
    @staticmethod
    def get_by_user_id(user_id: int) -> Optional['UserProfile']:
        """
        Get profile by Django user ID
        
        Args:
            user_id: Django user ID
            
        Returns:
            UserProfile or None
        """
        collection = get_collection(COLLECTION_USER_PROFILES)
        data = collection.find_one({'user_id': user_id})
        
        return UserProfile(data) if data else None
    
    @staticmethod
    def get_by_tenant(tenant_id: str, skip: int = 0, limit: int = 100) -> List['UserProfile']:
        """
        Get all profiles for a tenant
        
        Args:
            tenant_id: Tenant ID
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of UserProfile objects
        """
        collection = get_collection(COLLECTION_USER_PROFILES)
        cursor = collection.find({'tenant_id': tenant_id}).skip(skip).limit(limit)
        
        return [UserProfile(data) for data in cursor]
    
    @staticmethod
    def update(user_id: int, updates: dict) -> bool:
        """
        Update user profile
        
        Args:
            user_id: Django user ID
            updates: Fields to update
            
        Returns:
            bool: True if updated
        """
        collection = get_collection(COLLECTION_USER_PROFILES)
        
        updates['updated_at'] = datetime.utcnow()
        
        result = collection.update_one(
            {'user_id': user_id},
            {'$set': updates}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def update_last_login(user_id: int):
        """Update last login timestamp"""
        collection = get_collection(COLLECTION_USER_PROFILES)
        
        collection.update_one(
            {'user_id': user_id},
            {'$set': {'last_login': datetime.utcnow()}}
        )
    
    @staticmethod
    def delete(user_id: int) -> bool:
        """
        Delete user profile
        
        Args:
            user_id: Django user ID
            
        Returns:
            bool: True if deleted
        """
        collection = get_collection(COLLECTION_USER_PROFILES)
        result = collection.delete_one({'user_id': user_id})
        
        return result.deleted_count > 0
    
    @staticmethod
    def increment_api_usage(user_id: int, metric: str, amount: int = 1):
        """
        Increment API usage counter
        
        Args:
            user_id: Django user ID
            metric: Metric name (e.g., 'logs_uploaded', 'api_calls')
            amount: Amount to increment
        """
        collection = get_collection(COLLECTION_USER_PROFILES)
        
        collection.update_one(
            {'user_id': user_id},
            {
                '$inc': {f'api_quota.usage.{metric}': amount},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
    
    @staticmethod
    def get_quota_usage(user_id: int) -> dict:
        """
        Get API quota usage for user
        
        Args:
            user_id: Django user ID
            
        Returns:
            dict: Quota usage statistics
        """
        collection = get_collection(COLLECTION_USER_PROFILES)
        profile = collection.find_one(
            {'user_id': user_id},
            {'api_quota': 1}
        )
        
        return profile.get('api_quota', {}) if profile else {}


# Create indexes for user profiles
def create_user_profile_indexes():
    """Create MongoDB indexes for user profiles collection"""
    collection = get_collection(COLLECTION_USER_PROFILES)
    
    # Unique index on user_id
    collection.create_index('user_id', unique=True)
    
    # Index on tenant_id for multi-tenancy
    collection.create_index('tenant_id')
    
    # Compound index for tenant and role queries
    collection.create_index([('tenant_id', 1), ('role', 1)])
    
    # Index on created_at for sorting
    collection.create_index('created_at')
