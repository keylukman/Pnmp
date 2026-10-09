"""
Unit tests for monitoring calculator
"""
import pytest
from datetime import datetime, timedelta
from app.monitoring.calculator import TrafficCalculator


class TestTrafficCalculator:
    """Test traffic and utilization calculations"""
    
    def test_calculate_traffic_rate_first_poll(self):
        """Test that first poll returns None"""
        now = datetime.utcnow()
        bps, is_reset = TrafficCalculator.calculate_traffic_rate(
            current_counter=1000000,
            previous_counter=None,
            current_time=now,
            previous_time=None
        )
        assert bps is None
        assert is_reset is False
    
    def test_calculate_traffic_rate_normal(self):
        """Test normal traffic rate calculation"""
        now = datetime.utcnow()
        previous_time = now - timedelta(seconds=10)
        
        # 10 MB in 10 seconds = 8 Mbps
        bps, is_reset = TrafficCalculator.calculate_traffic_rate(
            current_counter=10000000,  # 10 MB
            previous_counter=0,
            current_time=now,
            previous_time=previous_time
        )
        
        assert bps == 8000000  # 8 Mbps
        assert is_reset is False
    
    def test_calculate_traffic_rate_counter_reset(self):
        """Test counter reset detection"""
        now = datetime.utcnow()
        previous_time = now - timedelta(seconds=10)
        
        # Counter went backwards (reset)
        bps, is_reset = TrafficCalculator.calculate_traffic_rate(
            current_counter=100,
            previous_counter=1000000,
            current_time=now,
            previous_time=previous_time
        )
        
        assert bps is None
        assert is_reset is True
    
    def test_calculate_traffic_rate_invalid_time(self):
        """Test invalid time delta"""
        now = datetime.utcnow()
        
        bps, is_reset = TrafficCalculator.calculate_traffic_rate(
            current_counter=1000000,
            previous_counter=0,
            current_time=now,
            previous_time=now  # Same time
        )
        
        assert bps is None
        assert is_reset is False
    
    def test_calculate_utilization_normal(self):
        """Test normal utilization calculation"""
        # 500 Mbps on 1 Gbps link = 50%
        util = TrafficCalculator.calculate_utilization(
            bps=500000000,
            speed_bps=1000000000
        )
        assert util == 50
    
    def test_calculate_utilization_over_100(self):
        """Test utilization clamped to 100"""
        util = TrafficCalculator.calculate_utilization(
            bps=1500000000,  # 1.5 Gbps
            speed_bps=1000000000  # 1 Gbps
        )
        assert util == 100
    
    def test_calculate_utilization_no_speed(self):
        """Test utilization with no speed info"""
        util = TrafficCalculator.calculate_utilization(
            bps=500000000,
            speed_bps=None
        )
        assert util is None
    
    def test_calculate_utilization_zero_speed(self):
        """Test utilization with zero speed"""
        util = TrafficCalculator.calculate_utilization(
            bps=500000000,
            speed_bps=0
        )
        assert util is None
    
    def test_calculate_utilization_no_bps(self):
        """Test utilization with no bps"""
        util = TrafficCalculator.calculate_utilization(
            bps=None,
            speed_bps=1000000000
        )
        assert util is None
    
    def test_calculate_interface_metrics_first_poll(self):
        """Test complete interface metrics calculation on first poll"""
        now = datetime.utcnow()
        
        metrics = TrafficCalculator.calculate_interface_metrics(
            current_rx_bytes=1000000,
            current_tx_bytes=500000,
            previous_rx_bytes=None,
            previous_tx_bytes=None,
            current_time=now,
            previous_time=None,
            speed_bps=1000000000
        )
        
        assert metrics['rx_bps'] is None
        assert metrics['tx_bps'] is None
        assert metrics['utilization_in'] is None
        assert metrics['utilization_out'] is None
        assert metrics['is_counter_reset'] is False
    
    def test_calculate_interface_metrics_normal(self):
        """Test complete interface metrics calculation"""
        now = datetime.utcnow()
        previous_time = now - timedelta(seconds=10)
        
        metrics = TrafficCalculator.calculate_interface_metrics(
            current_rx_bytes=10000000,  # 10 MB
            current_tx_bytes=5000000,   # 5 MB
            previous_rx_bytes=0,
            previous_tx_bytes=0,
            current_time=now,
            previous_time=previous_time,
            speed_bps=1000000000  # 1 Gbps
        )
        
        # 10 MB in 10 seconds = 8 Mbps RX
        assert metrics['rx_bps'] == 8000000
        # 5 MB in 10 seconds = 4 Mbps TX
        assert metrics['tx_bps'] == 4000000
        # 8 Mbps / 1 Gbps = 0.8%
        assert metrics['utilization_in'] == 0
        # 4 Mbps / 1 Gbps = 0.4%
        assert metrics['utilization_out'] == 0
        assert metrics['is_counter_reset'] is False
    
    def test_calculate_interface_metrics_counter_reset(self):
        """Test interface metrics with counter reset"""
        now = datetime.utcnow()
        previous_time = now - timedelta(seconds=10)
        
        metrics = TrafficCalculator.calculate_interface_metrics(
            current_rx_bytes=100,  # Counter went backwards
            current_tx_bytes=5000000,
            previous_rx_bytes=10000000,
            previous_tx_bytes=0,
            current_time=now,
            previous_time=previous_time,
            speed_bps=1000000000
        )
        
        assert metrics['rx_bps'] is None
        assert metrics['tx_bps'] == 4000000
        assert metrics['utilization_in'] is None
        assert metrics['utilization_out'] == 0
        assert metrics['is_counter_reset'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
