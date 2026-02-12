"""Configuration settings for the analyzer."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Application settings."""
    
    # Parser settings
    default_year: int = 2026
    log_file_patterns: List[str] = field(default_factory=lambda: ['*.log', '*.txt', 'logcat*'])
    
    # Analysis settings
    min_severity: str = 'info'
    enable_automotive_analysis: bool = True
    error_cluster_window_seconds: int = 60
    min_cluster_size: int = 3
    
    # Report settings
    max_sample_messages: int = 5
    max_top_tags: int = 20
    timeline_bucket_minutes: int = 5
    
    # Automotive-specific settings
    automotive_tags: Dict[str, List[str]] = field(default_factory=dict)
    custom_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, filepath: str) -> 'Settings':
        """Load settings from YAML file."""
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"Config file not found: {filepath}, using defaults")
            return cls()
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return cls()
    
    def to_yaml(self, filepath: str) -> None:
        """Save settings to YAML file."""
        from dataclasses import asdict
        
        with open(filepath, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)
    
    @classmethod
    def default(cls) -> 'Settings':
        """Get default settings."""
        return cls(
            automotive_tags={
                'vehicle': ['vehicle_hal', 'VehicleService', 'CarService', 'VehicleHal'],
                'power': ['CarPowerManagement', 'PowerManagerService', 'GarageModeService'],
                'audio': ['CarAudioService', 'AudioFlinger', 'CarAudioFocus'],
                'media': ['CarMediaService', 'MediaSession'],
                'cluster': ['ClusterHomeService', 'ClusterRenderingService'],
                'navigation': ['CarNavigationService', 'GnssLocationProvider'],
                'input': ['CarInputService', 'RotaryService', 'InputDispatcher'],
                'can': ['CanBusService', 'SocketCAN'],
            }
        )
