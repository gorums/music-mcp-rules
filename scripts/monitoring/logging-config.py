#!/usr/bin/env python3
"""
Logging Configuration for Music Collection MCP Server

This module provides comprehensive logging configuration for monitoring,
debugging, and maintaining the MCP server in different environments.
"""

import logging
import logging.handlers
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class MCPLoggingConfig:
    """Centralized logging configuration for Music Collection MCP Server."""
    
    # Log level mappings
    LOG_LEVELS = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG
    }
    
    # Default log formats
    FORMATS = {
        'detailed': '[%(asctime)s] %(name)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
        'simple': '%(asctime)s - %(levelname)s - %(message)s',
        'json': None,  # Will be handled by custom formatter
        'production': '[%(asctime)s] %(levelname)s - %(message)s'
    }
    
    def __init__(self, log_dir: Optional[str] = None, environment: str = "production"):
        """
        Initialize logging configuration.
        
        Args:
            log_dir: Directory for log files (if None, uses temp directory)
            environment: Deployment environment (development, testing, production)
        """
        self.environment = environment
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure based on environment
        self.config = self._get_environment_config()
        
    def _get_environment_config(self) -> Dict[str, Any]:
        """Get logging configuration based on environment."""
        
        configs = {
            'development': {
                'level': 'DEBUG',
                'format': 'detailed',
                'handlers': ['console', 'file', 'rotating'],
                'log_mcp_requests': True,
                'log_performance': True,
                'max_file_size': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5
            },
            'testing': {
                'level': 'INFO',
                'format': 'simple',
                'handlers': ['console', 'file'],
                'log_mcp_requests': False,
                'log_performance': False,
                'max_file_size': 5 * 1024 * 1024,  # 5MB
                'backup_count': 3
            },
            'production': {
                'level': 'ERROR',
                'format': 'production',
                'handlers': ['file', 'rotating'],
                'log_mcp_requests': False,
                'log_performance': False,
                'max_file_size': 50 * 1024 * 1024,  # 50MB
                'backup_count': 10
            }
        }
        
        return configs.get(self.environment, configs['production'])
    
    def setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging configuration."""
        
        # Create root logger
        logger = logging.getLogger('music_mcp')
        logger.setLevel(self.LOG_LEVELS[self.config['level']])
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Add configured handlers
        for handler_type in self.config['handlers']:
            handler = self._create_handler(handler_type)
            if handler:
                logger.addHandler(handler)
        
        # Setup specialized loggers
        self._setup_specialized_loggers()
        
        # Log initial configuration
        logger.info(f"Logging configured for {self.environment} environment")
        logger.info(f"Log level: {self.config['level']}")
        logger.info(f"Log directory: {self.log_dir}")
        
        return logger
    
    def _create_handler(self, handler_type: str) -> Optional[logging.Handler]:
        """Create specific log handler."""
        
        formatter = self._get_formatter()
        
        if handler_type == 'console':
            handler = logging.StreamHandler(sys.stdout)
            
        elif handler_type == 'file':
            log_file = self.log_dir / f"music_mcp_{datetime.now().strftime('%Y%m%d')}.log"
            handler = logging.FileHandler(log_file)
            
        elif handler_type == 'rotating':
            log_file = self.log_dir / "music_mcp.log"
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config['max_file_size'],
                backupCount=self.config['backup_count']
            )
            
        elif handler_type == 'error':
            log_file = self.log_dir / "music_mcp_errors.log"
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.ERROR)
            
        elif handler_type == 'performance':
            log_file = self.log_dir / "music_mcp_performance.log"
            handler = logging.FileHandler(log_file)
            
        else:
            return None
        
        handler.setFormatter(formatter)
        return handler
    
    def _get_formatter(self) -> logging.Formatter:
        """Get appropriate formatter for current configuration."""
        
        format_string = self.FORMATS[self.config['format']]
        
        if self.config['format'] == 'json':
            return JSONFormatter()
        else:
            return logging.Formatter(
                format_string,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    def _setup_specialized_loggers(self) -> None:
        """Setup specialized loggers for different components."""
        
        # MCP Request Logger
        if self.config['log_mcp_requests']:
            mcp_logger = logging.getLogger('music_mcp.requests')
            mcp_handler = logging.FileHandler(self.log_dir / "mcp_requests.log")
            mcp_handler.setFormatter(JSONFormatter())
            mcp_logger.addHandler(mcp_handler)
            mcp_logger.setLevel(logging.INFO)
        
        # Performance Logger
        if self.config['log_performance']:
            perf_logger = logging.getLogger('music_mcp.performance')
            perf_handler = logging.FileHandler(self.log_dir / "performance.log")
            perf_handler.setFormatter(JSONFormatter())
            perf_logger.addHandler(perf_handler)
            perf_logger.setLevel(logging.INFO)
        
        # Error Logger (always enabled)
        error_logger = logging.getLogger('music_mcp.errors')
        error_handler = logging.FileHandler(self.log_dir / "errors.log")
        error_handler.setFormatter(self._get_formatter())
        error_handler.setLevel(logging.ERROR)
        error_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger for specific component."""
        return logging.getLogger(f'music_mcp.{name}')


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON log output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class PerformanceLogger:
    """Specialized logger for performance monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger('music_mcp.performance')
        
    def log_operation(self, operation: str, duration: float, 
                     details: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics for an operation."""
        
        log_data = {
            'operation': operation,
            'duration_ms': duration * 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            log_data.update(details)
        
        # Create log record with extra fields
        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Performance metric',
            args=(),
            exc_info=None
        )
        record.extra_fields = log_data
        
        self.logger.handle(record)


class MCPRequestLogger:
    """Specialized logger for MCP request/response monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger('music_mcp.requests')
        
    def log_request(self, method: str, params: Dict[str, Any],
                   request_id: Optional[str] = None) -> None:
        """Log incoming MCP request."""
        
        log_data = {
            'type': 'request',
            'method': method,
            'params': params,
            'request_id': request_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self._log_mcp_data(log_data)
    
    def log_response(self, method: str, result: Any, duration: float,
                    request_id: Optional[str] = None) -> None:
        """Log MCP response."""
        
        log_data = {
            'type': 'response',
            'method': method,
            'duration_ms': duration * 1000,
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'result_size': len(str(result)) if result else 0
        }
        
        self._log_mcp_data(log_data)
    
    def log_error(self, method: str, error: str, duration: float,
                 request_id: Optional[str] = None) -> None:
        """Log MCP error."""
        
        log_data = {
            'type': 'error',
            'method': method,
            'error': error,
            'duration_ms': duration * 1000,
            'request_id': request_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self._log_mcp_data(log_data)
    
    def _log_mcp_data(self, log_data: Dict[str, Any]) -> None:
        """Log MCP data with JSON formatting."""
        
        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='MCP operation',
            args=(),
            exc_info=None
        )
        record.extra_fields = log_data
        
        self.logger.handle(record)


def setup_monitoring(environment: str = "production", 
                    log_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Setup complete monitoring configuration.
    
    Returns:
        Dictionary containing configured loggers and utilities
    """
    
    # Setup main logging
    logging_config = MCPLoggingConfig(log_dir=log_dir, environment=environment)
    main_logger = logging_config.setup_logging()
    
    # Create specialized loggers
    performance_logger = PerformanceLogger()
    request_logger = MCPRequestLogger()
    
    # Create monitoring utilities
    monitoring_utils = {
        'main_logger': main_logger,
        'performance_logger': performance_logger,
        'request_logger': request_logger,
        'get_logger': logging_config.get_logger,
        'log_dir': logging_config.log_dir
    }
    
    main_logger.info("Monitoring configuration complete")
    
    return monitoring_utils


def create_log_analysis_script() -> str:
    """Create a simple log analysis script."""
    
    script_content = '''#!/usr/bin/env python3
"""
Simple log analysis script for Music Collection MCP Server logs.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

def analyze_logs(log_dir):
    """Analyze MCP server logs."""
    
    log_dir = Path(log_dir)
    
    print("🔍 MCP Server Log Analysis")
    print("=" * 40)
    
    # Analyze error logs
    error_file = log_dir / "errors.log"
    if error_file.exists():
        print(f"\\n❌ Error Analysis:")
        with open(error_file) as f:
            errors = f.readlines()
        print(f"  Total errors: {len(errors)}")
        if errors:
            print(f"  Latest error: {errors[-1].strip()}")
    
    # Analyze performance logs
    perf_file = log_dir / "performance.log"
    if perf_file.exists():
        print(f"\\n🚀 Performance Analysis:")
        operations = []
        with open(perf_file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    operations.append(data)
                except json.JSONDecodeError:
                    continue
        
        if operations:
            durations = [op.get('duration_ms', 0) for op in operations]
            avg_duration = sum(durations) / len(durations)
            print(f"  Total operations: {len(operations)}")
            print(f"  Average duration: {avg_duration:.2f}ms")
            print(f"  Max duration: {max(durations):.2f}ms")
    
    # Analyze request logs
    req_file = log_dir / "mcp_requests.log"
    if req_file.exists():
        print(f"\\n📊 Request Analysis:")
        requests = []
        with open(req_file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    requests.append(data)
                except json.JSONDecodeError:
                    continue
        
        if requests:
            methods = [req.get('method', 'unknown') for req in requests]
            method_counts = Counter(methods)
            print(f"  Total requests: {len(requests)}")
            print("  Most used methods:")
            for method, count in method_counts.most_common(5):
                print(f"    {method}: {count}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_logs.py <log_directory>")
        sys.exit(1)
    
    analyze_logs(sys.argv[1])
'''
    
    return script_content


# Example usage configuration
if __name__ == "__main__":
    # Setup monitoring for development
    monitoring = setup_monitoring(environment="development")
    
    # Example usage
    logger = monitoring['main_logger']
    perf_logger = monitoring['performance_logger']
    req_logger = monitoring['request_logger']
    
    # Test logging
    logger.info("MCP Server starting up")
    
    # Test performance logging
    import time
    start_time = time.time()
    time.sleep(0.1)  # Simulate operation
    duration = time.time() - start_time
    perf_logger.log_operation("test_operation", duration, {"test_param": "value"})
    
    # Test request logging
    req_logger.log_request("scan_music_folders", {"path": "/music"}, "req-123")
    req_logger.log_response("scan_music_folders", {"bands": 10}, 0.5, "req-123")
    
    print(f"Logs written to: {monitoring['log_dir']}")
    
    # Create log analysis script
    analysis_script = create_log_analysis_script()
    script_path = monitoring['log_dir'] / "analyze_logs.py"
    with open(script_path, 'w') as f:
        f.write(analysis_script)
    
    print(f"Log analysis script created: {script_path}") 