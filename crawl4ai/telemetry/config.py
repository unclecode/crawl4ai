"""
Configuration management for Crawl4AI telemetry.
Handles user preferences and persistence.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum


class TelemetryConsent(Enum):
    """Telemetry consent levels."""
    NOT_SET = "not_set"
    DENIED = "denied"
    ONCE = "once"  # Send current error only
    ALWAYS = "always"  # Send all errors


class TelemetryConfig:
    """Manages telemetry configuration and persistence."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Optional custom config directory
        """
        if config_dir:
            self.config_dir = config_dir
        else:
            # Default to ~/.crawl4ai/
            self.config_dir = Path.home() / '.crawl4ai'
        
        self.config_file = self.config_dir / 'config.json'
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> None:
        """Load configuration from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                # Corrupted or inaccessible config - start fresh
                self._config = {}
        else:
            self._config = {}
    
    def _save_config(self) -> bool:
        """
        Save configuration to disk.
        
        Returns:
            True if saved successfully
        """
        try:
            self._ensure_config_dir()
            
            # Write to temporary file first
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.config_file)
            return True
            
        except (IOError, OSError):
            return False
    
    def get_telemetry_settings(self) -> Dict[str, Any]:
        """
        Get current telemetry settings.
        
        Returns:
            Dictionary with telemetry settings
        """
        return self._config.get('telemetry', {
            'consent': TelemetryConsent.NOT_SET.value,
            'email': None
        })
    
    def get_consent(self) -> TelemetryConsent:
        """
        Get current consent status.
        
        Returns:
            TelemetryConsent enum value
        """
        settings = self.get_telemetry_settings()
        consent_value = settings.get('consent', TelemetryConsent.NOT_SET.value)
        
        # Handle legacy boolean values
        if isinstance(consent_value, bool):
            consent_value = TelemetryConsent.ALWAYS.value if consent_value else TelemetryConsent.DENIED.value
        
        try:
            return TelemetryConsent(consent_value)
        except ValueError:
            return TelemetryConsent.NOT_SET
    
    def set_consent(
        self, 
        consent: TelemetryConsent, 
        email: Optional[str] = None
    ) -> bool:
        """
        Set telemetry consent and optional email.
        
        Args:
            consent: Consent level
            email: Optional email for follow-up
            
        Returns:
            True if saved successfully
        """
        if 'telemetry' not in self._config:
            self._config['telemetry'] = {}
        
        self._config['telemetry']['consent'] = consent.value
        
        # Only update email if provided
        if email is not None:
            self._config['telemetry']['email'] = email
        
        return self._save_config()
    
    def get_email(self) -> Optional[str]:
        """
        Get stored email if any.
        
        Returns:
            Email address or None
        """
        settings = self.get_telemetry_settings()
        return settings.get('email')
    
    def is_enabled(self) -> bool:
        """
        Check if telemetry is enabled.
        
        Returns:
            True if telemetry should send data
        """
        consent = self.get_consent()
        return consent in [TelemetryConsent.ONCE, TelemetryConsent.ALWAYS]
    
    def should_send_current(self) -> bool:
        """
        Check if current error should be sent.
        Used for one-time consent.
        
        Returns:
            True if current error should be sent
        """
        consent = self.get_consent()
        if consent == TelemetryConsent.ONCE:
            # After sending once, reset to NOT_SET
            self.set_consent(TelemetryConsent.NOT_SET)
            return True
        return consent == TelemetryConsent.ALWAYS
    
    def clear(self) -> bool:
        """
        Clear all telemetry settings.
        
        Returns:
            True if cleared successfully
        """
        if 'telemetry' in self._config:
            del self._config['telemetry']
            return self._save_config()
        return True
    
    def update_from_env(self) -> None:
        """Update configuration from environment variables."""
        # Check for telemetry disable flag
        if os.environ.get('CRAWL4AI_TELEMETRY') == '0':
            self.set_consent(TelemetryConsent.DENIED)
        
        # Check for email override
        env_email = os.environ.get('CRAWL4AI_TELEMETRY_EMAIL')
        if env_email and self.is_enabled():
            current_settings = self.get_telemetry_settings()
            self.set_consent(
                TelemetryConsent(current_settings['consent']),
                email=env_email
            )