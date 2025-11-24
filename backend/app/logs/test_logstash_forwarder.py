import pytest
from unittest.mock import Mock, patch, MagicMock
from django.conf import settings
from app.logs.logstash_forwarder import LogstashForwarder, get_logstash_forwarder
import socket
import json


class TestLogstashForwarder:
    """Test suite for LogstashForwarder"""
    
    def test_forwarder_initialization(self):
        """Test forwarder is initialized with correct settings"""
        forwarder = LogstashForwarder(
            host='localhost',
            port=5000,
            protocol='tcp',
            timeout=5,
            max_retries=3
        )
        
        assert forwarder.host == 'localhost'
        assert forwarder.port == 5000
        assert forwarder.protocol == 'tcp'
        assert forwarder.timeout == 5
        assert forwarder.max_retries == 3
        assert forwarder.socket is None
    
    def test_forwarder_default_settings(self):
        """Test forwarder uses default settings from Django config"""
        with patch.object(settings, 'LOGSTASH_HOST', 'logstash'):
            with patch.object(settings, 'LOGSTASH_PORT', 5000):
                forwarder = LogstashForwarder()
                
                assert forwarder.host == 'logstash'
                assert forwarder.port == 5000
    
    @patch('socket.socket')
    def test_tcp_connection_success(self, mock_socket):
        """Test successful TCP connection"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder(protocol='tcp')
        success = forwarder.connect()
        
        assert success is True
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_sock.settimeout.assert_called_once()
        mock_sock.connect.assert_called_once()
    
    @patch('socket.socket')
    def test_udp_connection_success(self, mock_socket):
        """Test successful UDP connection"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder(protocol='udp')
        success = forwarder.connect()
        
        assert success is True
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
    
    @patch('socket.socket')
    def test_connection_failure(self, mock_socket):
        """Test connection failure handling"""
        mock_socket.side_effect = ConnectionRefusedError("Connection refused")
        
        forwarder = LogstashForwarder()
        success = forwarder.connect()
        
        assert success is False
        assert forwarder._stats['last_error'] is not None
    
    @patch('socket.socket')
    def test_send_single_log_tcp(self, mock_socket):
        """Test sending single log via TCP"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder(protocol='tcp')
        forwarder.connect()
        
        log_entry = {
            'message': 'Test log',
            'level': 'INFO',
            '@timestamp': '2025-11-24T10:00:00Z'
        }
        
        success = forwarder.send_log(log_entry)
        
        assert success is True
        mock_sock.sendall.assert_called_once()
        
        # Verify JSON formatting
        sent_data = mock_sock.sendall.call_args[0][0]
        assert sent_data.endswith(b'\n')
        parsed = json.loads(sent_data.decode('utf-8').strip())
        assert parsed['message'] == 'Test log'
    
    @patch('socket.socket')
    def test_send_multiple_logs(self, mock_socket):
        """Test sending multiple logs"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder()
        forwarder.connect()
        
        logs = [
            {'message': 'Log 1', 'level': 'INFO'},
            {'message': 'Log 2', 'level': 'ERROR'},
            {'message': 'Log 3', 'level': 'WARNING'}
        ]
        
        success = forwarder.send_logs(logs)
        
        assert success is True
        assert mock_sock.sendall.call_count == 3
        assert forwarder._stats['total_sent'] == 3
    
    @patch('socket.socket')
    def test_send_logs_with_retry(self, mock_socket):
        """Test retry logic on connection failure"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        # First attempt fails, second succeeds
        mock_sock.sendall.side_effect = [
            ConnectionError("Connection lost"),
            None  # Success on retry
        ]
        
        forwarder = LogstashForwarder(max_retries=1, retry_delay=0.1)
        
        with patch('time.sleep'):  # Skip actual sleep
            success = forwarder.send_logs([{'message': 'Test'}])
        
        assert success is True
        assert forwarder._stats['total_retries'] >= 1
    
    @patch('socket.socket')
    def test_send_logs_retry_exhausted(self, mock_socket):
        """Test failure after all retries exhausted"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.sendall.side_effect = ConnectionError("Connection lost")
        
        forwarder = LogstashForwarder(max_retries=2, retry_delay=0.1)
        
        with patch('time.sleep'):
            success = forwarder.send_logs([{'message': 'Test'}])
        
        assert success is False
        assert forwarder._stats['total_failed'] == 1
        assert forwarder._stats['last_error'] is not None
    
    @patch('socket.socket')
    def test_batch_sending(self, mock_socket):
        """Test batch sending functionality"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder()
        forwarder.connect()
        
        # Create 250 logs, send in batches of 100
        logs = [{'message': f'Log {i}'} for i in range(250)]
        
        result = forwarder.send_batch(logs, batch_size=100)
        
        assert result['sent'] == 250
        assert result['failed'] == 0
        assert result['total'] == 250
    
    @patch('socket.socket')
    def test_health_check_healthy(self, mock_socket):
        """Test health check when connection is healthy"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder()
        health = forwarder.health_check()
        
        assert health['status'] == 'healthy'
        assert health['connected'] is True
        assert health['host'] == forwarder.host
        assert health['port'] == forwarder.port
    
    @patch('socket.socket')
    def test_health_check_unhealthy(self, mock_socket):
        """Test health check when connection fails"""
        mock_socket.side_effect = ConnectionRefusedError("Connection refused")
        
        forwarder = LogstashForwarder()
        health = forwarder.health_check()
        
        assert health['status'] == 'unhealthy'
        assert health['connected'] is False
        assert 'error' in health
    
    @patch('socket.socket')
    def test_statistics_tracking(self, mock_socket):
        """Test statistics are properly tracked"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder()
        forwarder.connect()
        
        # Send some logs
        forwarder.send_logs([{'message': 'Log 1'}, {'message': 'Log 2'}])
        
        stats = forwarder.get_statistics()
        
        assert stats['total_sent'] == 2
        assert stats['total_failed'] == 0
        assert stats['success_rate'] == 1.0
        assert stats['last_success'] is not None
    
    def test_statistics_reset(self):
        """Test statistics can be reset"""
        forwarder = LogstashForwarder()
        
        # Manually set some stats
        forwarder._stats['total_sent'] = 100
        forwarder._stats['total_failed'] = 5
        
        forwarder.reset_statistics()
        
        assert forwarder._stats['total_sent'] == 0
        assert forwarder._stats['total_failed'] == 0
        assert forwarder._stats['last_error'] is None
    
    @patch('socket.socket')
    def test_context_manager(self, mock_socket):
        """Test forwarder works as context manager"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        with LogstashForwarder() as forwarder:
            forwarder.send_log({'message': 'Test'})
        
        # Socket should be closed after context exit
        mock_sock.close.assert_called_once()
    
    @patch('socket.socket')
    def test_disconnect(self, mock_socket):
        """Test disconnect closes socket"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder()
        forwarder.connect()
        forwarder.disconnect()
        
        mock_sock.close.assert_called_once()
        assert forwarder.socket is None
    
    @patch('socket.socket')
    def test_send_empty_log_list(self, mock_socket):
        """Test sending empty log list"""
        forwarder = LogstashForwarder()
        success = forwarder.send_logs([])
        
        assert success is True
        assert forwarder._stats['total_sent'] == 0
    
    @patch('socket.socket')
    def test_udp_sending(self, mock_socket):
        """Test UDP sending uses sendto instead of sendall"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder(protocol='udp')
        forwarder.connect()
        
        log_entry = {'message': 'UDP test'}
        forwarder.send_log(log_entry)
        
        mock_sock.sendto.assert_called_once()
    
    def test_invalid_protocol(self):
        """Test invalid protocol raises error"""
        forwarder = LogstashForwarder(protocol='invalid')
        success = forwarder.connect()
        
        assert success is False
        assert 'Unsupported protocol' in forwarder._stats['last_error']
    
    @patch('socket.socket')
    def test_unicode_handling(self, mock_socket):
        """Test handling of unicode characters in logs"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        forwarder = LogstashForwarder()
        forwarder.connect()
        
        log_entry = {
            'message': 'Test with unicode: 日本語 🎉',
            'level': 'INFO'
        }
        
        success = forwarder.send_log(log_entry)
        
        assert success is True
        sent_data = mock_sock.sendall.call_args[0][0]
        # Should be properly encoded UTF-8
        assert isinstance(sent_data, bytes)


class TestLogstashForwarderSingleton:
    """Test singleton instance management"""
    
    def test_get_singleton_instance(self):
        """Test get_logstash_forwarder returns singleton"""
        forwarder1 = get_logstash_forwarder()
        forwarder2 = get_logstash_forwarder()
        
        assert forwarder1 is forwarder2
    
    @patch.object(settings, 'LOGSTASH_HOST', 'test-host')
    @patch.object(settings, 'LOGSTASH_PORT', 9999)
    def test_singleton_uses_settings(self):
        """Test singleton uses Django settings"""
        # Clear any existing singleton
        import app.logs.logstash_forwarder as lf_module
        lf_module._logstash_forwarder = None
        
        forwarder = get_logstash_forwarder()
        
        assert forwarder.host == 'test-host'
        assert forwarder.port == 9999
