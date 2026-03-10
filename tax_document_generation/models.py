"""
Data Models Module

This module defines data models for the tax document generation feature.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict
from exceptions import ValidationError


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class JobRecord:
    """
    Represents a document generation job record.
    """
    job_id: str
    user_id: str
    document_type: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    template_key: str
    completed_at: Optional[datetime] = None
    output_key: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dynamodb_item(self) -> Dict:
        """
        Convert to DynamoDB item format.
        
        Returns:
            dict: DynamoDB item representation
        """
        item = {
            "jobId": self.job_id,
            "userId": self.user_id,
            "documentType": self.document_type,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "createdAt": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updatedAt": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "templateKey": self.template_key
        }
        
        if self.completed_at:
            item["completedAt"] = self.completed_at.isoformat() if isinstance(self.completed_at, datetime) else self.completed_at
        
        if self.output_key:
            item["outputKey"] = self.output_key
        
        if self.error_message:
            item["errorMessage"] = self.error_message
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict) -> 'JobRecord':
        """
        Create JobRecord from DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            JobRecord: Parsed job record
        """
        return cls(
            job_id=item['jobId'],
            user_id=item['userId'],
            document_type=item['documentType'],
            status=JobStatus(item['status']),
            created_at=datetime.fromisoformat(item['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(item['updatedAt'].replace('Z', '+00:00')),
            template_key=item['templateKey'],
            completed_at=datetime.fromisoformat(item['completedAt'].replace('Z', '+00:00')) if 'completedAt' in item else None,
            output_key=item.get('outputKey'),
            error_message=item.get('errorMessage')
        )


@dataclass
class GenerationRequest:
    """
    Represents a document generation request from the API.
    """
    document_type: str
    form_data: Dict
    
    @classmethod
    def from_api_event(cls, event: Dict) -> 'GenerationRequest':
        """
        Parse from API Gateway event.
        
        Args:
            event: API Gateway event dictionary
            
        Returns:
            GenerationRequest: Parsed request
            
        Raises:
            ValidationError: If request body is invalid
        """
        try:
            body = event.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
            
            document_type = body.get('documentType')
            form_data = body.get('formData', {})
            
            if not document_type:
                raise ValidationError("Missing required field: documentType")
            
            if not isinstance(form_data, dict):
                raise ValidationError("formData must be a dictionary")
            
            return cls(
                document_type=document_type,
                form_data=form_data
            )
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in request body: {str(e)}")
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to parse request: {str(e)}")


@dataclass
class ValidationResult:
    """
    Represents the result of a validation operation.
    """
    is_valid: bool
    errors: list
    
    def raise_if_invalid(self) -> None:
        """
        Raise ValidationError if validation failed.
        
        Raises:
            ValidationError: If is_valid is False
        """
        if not self.is_valid:
            error_message = ", ".join(self.errors) if self.errors else "Validation failed"
            raise ValidationError(error_message)
