"""Android Automotive-specific log analyzer."""

from typing import List, Dict
import logging

from .pattern_analyzer import PatternAnalyzer, PatternRule
from ..models import LogEntry, AnalysisResult, Severity

logger = logging.getLogger(__name__)


class AutomotiveAnalyzer(PatternAnalyzer):
    """
    Specialized analyzer for Android Automotive logs.
    
    Includes patterns specific to:
    - Vehicle HAL
    - Car Services (Audio, Media, Power, Navigation)
    - Instrument Cluster
    - CAN/LIN bus communication
    - ADAS systems
    """
    
    # Android Automotive-specific patterns
    AUTOMOTIVE_PATTERNS = [
        # Vehicle HAL
        PatternRule(
            name='vehicle_hal_error',
            regex=r'VehicleHal.*error|VHAL.*fail|vehicle_service.*error|VehicleProperty.*invalid',
            tags=['vehicle_hal', 'VehicleService', 'CarService', 'VehicleHal'],
            severity=Severity.ERROR,
            description='Vehicle HAL communication or property error',
            recommendation='Check VHAL service status, verify vehicle properties, and CAN bus connectivity'
        ),
        PatternRule(
            name='vhal_timeout',
            regex=r'VHAL.*timeout|VehicleHal.*timeout|vehicle.*property.*timeout',
            tags=['VehicleHal', 'CarService'],
            severity=Severity.ERROR,
            description='Vehicle HAL operation timed out',
            recommendation='Check ECU responsiveness and CAN bus load'
        ),
        
        # Car Power Management
        PatternRule(
            name='power_state_error',
            regex=r'CarPowerManagement.*(unexpected|failed|timeout|invalid)|PowerHal.*error',
            tags=['CarPowerManagement', 'PowerManagerService', 'CarPowerManagerService'],
            severity=Severity.ERROR,
            description='Power state transition error',
            recommendation='Review power state machine transitions and check for blocking operations'
        ),
        PatternRule(
            name='deep_sleep_issue',
            regex=r'deep sleep.*(fail|abort|cancel)|suspend.*fail|cannot enter.*sleep',
            tags=['CarPowerManagement', 'PowerManagerService', 'SuspendControl'],
            severity=Severity.WARNING,
            description='Deep sleep entry issue - may cause battery drain',
            recommendation='Check for wakelocks blocking sleep and review suspend blockers'
        ),
        PatternRule(
            name='garage_mode_issue',
            regex=r'GarageMode.*(fail|timeout|cancel)|garage.*mode.*error',
            tags=['GarageModeService', 'CarService'],
            severity=Severity.WARNING,
            description='Garage mode operation issue',
            recommendation='Review garage mode jobs and timeout settings'
        ),
        
        # Car Audio
        PatternRule(
            name='audio_focus_conflict',
            regex=r'CarAudioService.*focus.*(reject|deny|conflict|fail)|audio.*focus.*lost',
            tags=['CarAudioService', 'AudioFlinger', 'AudioService', 'CarAudioFocus'],
            severity=Severity.WARNING,
            description='Audio focus conflict detected',
            recommendation='Review audio focus handling policy and priority matrix'
        ),
        PatternRule(
            name='audio_zone_error',
            regex=r'audio.*zone.*(error|invalid|fail)|CarAudioZone.*error',
            tags=['CarAudioService', 'CarAudioZone'],
            severity=Severity.ERROR,
            description='Audio zone configuration or routing error',
            recommendation='Verify audio zone configuration in car_audio_configuration.xml'
        ),
        
        # Instrument Cluster
        PatternRule(
            name='cluster_disconnect',
            regex=r'ClusterHomeService.*(disconnected|unavailable|error)|InstrumentCluster.*(fail|disconnect)',
            tags=['ClusterHomeService', 'ClusterRenderingService', 'InstrumentClusterService'],
            severity=Severity.ERROR,
            description='Instrument cluster disconnection or communication failure',
            recommendation='Check cluster display connection and rendering service'
        ),
        PatternRule(
            name='cluster_render_error',
            regex=r'ClusterRender.*(fail|error|timeout)|cluster.*display.*(error|fail)',
            tags=['ClusterRenderingService', 'InstrumentClusterRenderer'],
            severity=Severity.ERROR,
            description='Cluster rendering error',
            recommendation='Check GPU resources and cluster rendering pipeline'
        ),
        
        # CAN/LIN Bus
        PatternRule(
            name='can_bus_error',
            regex=r'CAN.*(error|timeout|overflow|busoff|warning)|SocketCAN.*(error|fail)',
            tags=['CanBusService', 'SocketCAN', 'CanController'],
            severity=Severity.CRITICAL,
            description='CAN bus communication error',
            recommendation='Check CAN bus wiring, termination resistors, and ECU status'
        ),
        PatternRule(
            name='can_frame_error',
            regex=r'CAN.*frame.*(invalid|corrupt|error)|bad.*CAN.*message',
            tags=['CanBusService', 'VehicleHal'],
            severity=Severity.ERROR,
            description='Invalid CAN frame received',
            recommendation='Verify CAN database (DBC) configuration and check for EMI issues'
        ),
        PatternRule(
            name='lin_bus_error',
            regex=r'LIN.*(error|timeout|fail)|LinBus.*(error|fail)',
            tags=['LinBusService', 'LinController'],
            severity=Severity.ERROR,
            description='LIN bus communication error',
            recommendation='Check LIN master/slave configuration and bus load'
        ),
        
        # Navigation & Location
        PatternRule(
            name='navigation_error',
            regex=r'CarNavigationService.*(error|fail)|navigation.*(fail|unavailable)',
            tags=['CarNavigationService', 'NavigationService'],
            severity=Severity.WARNING,
            description='Navigation service error',
            recommendation='Check GPS signal and navigation data provider'
        ),
        PatternRule(
            name='gnss_error',
            regex=r'GNSS.*(error|fail|timeout)|GPS.*(fail|no.*fix|lost)',
            tags=['GnssLocationProvider', 'LocationManager'],
            severity=Severity.WARNING,
            description='GNSS/GPS positioning error',
            recommendation='Check GNSS antenna and satellite visibility'
        ),
        
        # CarService general
        PatternRule(
            name='car_service_crash',
            regex=r'CarService.*(crash|died|restart)|car.*service.*exception',
            tags=['CarService', 'system_server'],
            severity=Severity.CRITICAL,
            description='CarService crash detected',
            recommendation='Collect car service crash dump and review stack trace'
        ),
        PatternRule(
            name='car_watchdog_timeout',
            regex=r'CarWatchdog.*(timeout|unresponsive)|car.*watchdog.*kill',
            tags=['CarWatchdogService', 'CarWatchdog'],
            severity=Severity.CRITICAL,
            description='Car Watchdog detected unresponsive process',
            recommendation='Identify hung process and fix blocking operation'
        ),
        
        # Input & HMI
        PatternRule(
            name='rotary_input_error',
            regex=r'RotaryService.*(error|fail)|rotary.*input.*(fail|invalid)',
            tags=['CarInputService', 'RotaryService'],
            severity=Severity.WARNING,
            description='Rotary controller input error',
            recommendation='Check rotary controller connection and configuration'
        ),
        PatternRule(
            name='evs_error',
            regex=r'EVS.*(error|fail|timeout)|ExtVehicleService.*(fail|error)|camera.*(fail|disconnect)',
            tags=['EvsManager', 'EvsService', 'CarEvsService'],
            severity=Severity.ERROR,
            description='External Vehicle Service (camera) error',
            recommendation='Check camera connections and EVS HAL status'
        ),
        
        # OTA & Updates
        PatternRule(
            name='ota_update_error',
            regex=r'OTA.*(fail|error|abort)|update.*(fail|error).*automotive',
            tags=['UpdateEngine', 'OtaUpdateService'],
            severity=Severity.ERROR,
            description='OTA update error',
            recommendation='Check update package integrity and storage space'
        ),
    ]
    
    # Key Android Automotive tags to monitor
    AUTOMOTIVE_TAGS = {
        'vehicle': ['vehicle_hal', 'VehicleService', 'CarService', 'VehicleHal'],
        'power': ['CarPowerManagement', 'PowerManagerService', 'CarPowerManagerService', 'GarageModeService'],
        'audio': ['CarAudioService', 'AudioFlinger', 'CarAudioFocus', 'CarAudioZone'],
        'media': ['CarMediaService', 'MediaSession', 'CarMediaBrowseService'],
        'cluster': ['ClusterHomeService', 'ClusterRenderingService', 'InstrumentClusterService'],
        'navigation': ['CarNavigationService', 'GnssLocationProvider'],
        'input': ['CarInputService', 'RotaryService', 'InputDispatcher'],
        'connectivity': ['CarBluetoothService', 'CarWifiService', 'CarTelemetryService'],
        'evs': ['EvsManager', 'EvsService', 'CarEvsService'],
        'can': ['CanBusService', 'SocketCAN', 'VehicleHal'],
    }
    
    def __init__(self):
        """Initialize with automotive-specific patterns."""
        super().__init__(custom_patterns=self.AUTOMOTIVE_PATTERNS)
    
    def analyze(self, entries: List[LogEntry]) -> List[AnalysisResult]:
        """
        Analyze log entries with automotive-specific patterns.
        
        Args:
            entries: List of log entries
            
        Returns:
            List of analysis results sorted by severity
        """
        # Run base pattern analysis
        results = super().analyze(entries)
        
        # Add any automotive-specific aggregate analysis
        boot_issues = self._analyze_boot_sequence(entries)
        if boot_issues:
            results.extend(boot_issues)
        
        return sorted(results)
    
    def _analyze_boot_sequence(self, entries: List[LogEntry]) -> List[AnalysisResult]:
        """Analyze automotive boot sequence for issues."""
        issues = []
        
        # Look for late service starts
        car_service_entries = [e for e in entries if 'CarService' in e.tag]
        if car_service_entries:
            first_entry = car_service_entries[0]
            # Check if boot took too long (simple heuristic)
            boot_messages = [e for e in entries if 'boot completed' in e.message.lower()]
            
            if boot_messages and car_service_entries:
                boot_time = boot_messages[0].timestamp
                car_start = car_service_entries[0].timestamp
                delta = (car_start - entries[0].timestamp).total_seconds()
                
                if delta > 30:  # CarService should start within 30 seconds
                    issues.append(AnalysisResult(
                        category='slow_boot_sequence',
                        severity=Severity.WARNING,
                        description=f'CarService took {delta:.1f}s to start',
                        recommendation='Optimize boot sequence and review init dependencies',
                        occurrences=1,
                        first_seen=first_entry.timestamp_str
                    ))
        
        return issues
    
    def get_automotive_summary(self, entries: List[LogEntry]) -> Dict:
        """
        Get automotive-specific summary.
        
        Args:
            entries: List of log entries
            
        Returns:
            Summary dictionary with automotive metrics
        """
        summary = {
            'subsystem_activity': {},
            'vehicle_property_errors': 0,
            'power_transitions': 0,
            'can_errors': 0,
        }
        
        for category, tags in self.AUTOMOTIVE_TAGS.items():
            category_entries = [e for e in entries if e.tag in tags]
            error_count = sum(1 for e in category_entries if e.is_error)
            
            summary['subsystem_activity'][category] = {
                'total': len(category_entries),
                'errors': error_count
            }
        
        # Count specific issues
        summary['vehicle_property_errors'] = sum(
            1 for e in entries if 'VehicleProperty' in e.message and e.is_error
        )
        summary['power_transitions'] = sum(
            1 for e in entries if 'power state' in e.message.lower()
        )
        summary['can_errors'] = sum(
            1 for e in entries if 'CAN' in e.tag and e.is_error
        )
        
        return summary
