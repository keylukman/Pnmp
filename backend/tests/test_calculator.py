"""
Unit tests for TrafficCalculator
"""
import pytest
from datetime import datetime, timedelta
from app.monitoring.calculator import TrafficCalculator


class TestTrafficCalculator:
    """Test traffic rate and utilization calculations"""
    
    def test_calculate_traffic_rate_first_poll(self):
        """Test first poll returns None"""
        current_time = datetime.utcnow()
        bps, is_reset = TrafficCalculator.calculate_traffic_rate(
            current_counter=1000000,
            previous_counter=None,
            current_time=current_time,
            previous_time=None
        )
        assert bps is None
        assert is_reset is False
    
    def test_calculate_traffic_rate_normal(self):
        """Test normal traffic calculation"""
        previous_time = datetime.utcnow() - timedelta(seconds=10)
        current_time = datetime.utcnow()
        
        # 10 MB in 10 seconds = 8 Mbps
        bps, is_reset = TrafficCalculator.calculate_traffic_rate(
            current_counter=11000000,  # 11 MB
            previous_counter=1000000,  # 1 MB
            current_time=current_time,
            previous_time=previous_time
        )
        
        assert bps is not None
        assert is_reset is False
        # 10 MB * 8 bits = 80 MB bits / 10 seconds = 8 Mbps
        assert bps == 8000000
    
    def test_calculate_traffic_rate_counter_reset(self):
        """Test counter reset detection"""
        previous_time = datetime.utcnow() - timedelta(seconds=10)
        current_time = datetime.utcnow()
        
        # Counter decreased (device reboot)
        bps, is_reset = TrafficCalculator.calculate_traffic_rate(
            current_counter=500000,   # Lower than previous
            previous_counter=1000000,
            current_time=current_time,
            previous_time=previous_time
        )
        
        assert bps is None
        assert is_reset is True
    
    def test_calculate_traffic_rate_zero_time_delta(self):
        """Test zero time delta"""
        current_time = datetime.utcnow()
        
        bps, is_reset = TrafficCalculator.calculate_traffic_rate(
            current_counter=2000000,
            previous_counter=1000000,
            current_time=current_time,
            previous_time=current_time  # Same time
        )
        
        assert bps is None
        assert is_reset is False
    
    def test_calculate_utilization_normal(self):
        """Test normal utilization calculation"""
        # 500 Mbps on 1 Gbps link = 50%
        utilization = TrafficCalculator.calculate_utilization(
            bps=500000000,
            speed_bps=1000000000
        )
        assert utilization == 50
    
    def test_calculate_utilization_none_bps(self):
        """Test utilization with None bps"""
        utilization = TrafficCalculator.calculate_utilization(
            bps=None,
            speed_bps=1000000000
        )
        assert utilization is None
    
    def test_calculate_utilization_none_speed(self):
        """Test utilization with None speed"""
        utilization = TrafficCalculator.calculate_utilization(
            bps=500000000,
            speed_bps=None
        )
        assert utilization is None
    
    def test_calculate_utilization_zero_speed(self):
        """Test utilization with zero speed"""
        utilization = TrafficCalculator.calculate_utilization(
            bps=500000000,
            speed_bps=0
        )
        assert utilization is None
    
    def test_calculate_utilization_over_100(self):
        """Test utilization clamped to 100"""
        # 1.5 Gbps on 1 Gbps link = 150% -> clamped to 100%
        utilization = TrafficCalculator.calculate_utilization(
            bps=1500000000,
            speed_bps=1000000000
        )
        assert utilization == 100
    
    def test_calculate_interface_metrics_first_poll(self):
        """Test interface metrics on first poll"""
        current_time = datetime.utcnow()
        
        metrics = TrafficCalculator.calculate_interface_metrics(
            current_rx_bytes=1000000,
            current_tx_bytes=500000,
            previous_rx_bytes=None,
            previous_tx_bytes=None,
            current_time=current_time,
            previous_time=None,
            speed_bps=1000000000
        )
        
        assert metrics['rx_bps'] is None
        assert metrics['tx_bps'] is None
        assert metrics['utilization_in'] is None
        assert metrics['utilization_out'] is None
        assert metrics['is_counter_reset'] is False
    
    def test_calculate_interface_metrics_normal(self):
        """Test normal interface metrics calculation"""
        previous_time = datetime.utcnow() - timedelta(seconds=10)
        current_time = datetime.utcnow()
        
        metrics = TrafficCalculator.calculate_interface_metrics(
            current_rx_bytes=11000000,  # 11 MB
            current_tx_bytes=6000000,   # 6 MB
            previous_rx_bytes=1000000,  # 1 MB
            previous_tx_bytes=1000000,  # 1 MB
            current_time=current_time,
            previous_time=previous_time,
            speed_bps=1000000000  # 1 Gbps
        )
        
        # RX: 10 MB in 10s = 8 Mbps = 0.8%
        assert metrics['rx_bps'] == 8000000
        assert metrics['utilization_in'] == 0
        
        # TX: 5 MB in 10s = 4 Mbps = 0.4%
        assert metrics['tx_bps'] == 4000000
        assert metrics['utilization_out'] == 0
        
        assert metrics['is_counter_reset'] is False
    
    def test_calculate_interface_metrics_counter_reset(self):
        """Test interface metrics with counter reset"""
        previous_time = datetime.utcnow() - timedelta(seconds=10)
        current_time = datetime.utcnow()
        
        metrics = TrafficCalculator.calculate_interface_metrics(
            current_rx_bytes=500000,   # Lower than previous
            current_tx_bytes=6000000,
            previous_rx_bytes=1000000,
            previous_tx_bytes=1000000,
            current_time=current_time,
            previous_time=previous_time,
            speed_bps=1000000000
        )
        
        assert metrics['rx_bps'] is None
        assert metrics['is_counter_reset'] is True
