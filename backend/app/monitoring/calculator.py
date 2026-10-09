"""
Traffic and utilization calculator for monitoring metrics
"""
from typing import Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TrafficCalculator:
    """
    Calculates traffic rates and utilization from SNMP counters.
    Handles counter rollover and reset scenarios properly.
    """
    
    @staticmethod
    def calculate_traffic_rate(
        current_counter: int,
        previous_counter: Optional[int],
        current_time: datetime,
        previous_time: Optional[datetime]
    ) -> Tuple[Optional[int], bool]:
        """
        Calculate traffic rate in bits per second.
        
        Args:
            current_counter: Current counter value (bytes)
            previous_counter: Previous counter value (bytes), None if first poll
            current_time: Current timestamp
            previous_time: Previous timestamp, None if first poll
            
        Returns:
            Tuple of (bps: Optional[int], is_counter_reset: bool)
            - bps: Bits per second, None if cannot calculate
            - is_counter_reset: True if counter reset/rollover detected
        """
        # First poll - cannot calculate
        if previous_counter is None or previous_time is None:
            return None, False
        
        # Calculate time delta
        time_delta = (current_time - previous_time).total_seconds()
        
        if time_delta <= 0:
            logger.warning(f"Invalid time delta: {time_delta}s")
            return None, False
        
        # Calculate byte delta
        byte_delta = current_counter - previous_counter
        
        # Handle counter rollover/reset
        if byte_delta < 0:
            logger.warning(
                f"Counter reset detected: current={current_counter}, "
                f"previous={previous_counter}, delta={byte_delta}"
            )
            return None, True
        
        # Calculate bits per second
        bps = int((byte_delta * 8) / time_delta)
        
        return bps, False
    
    @staticmethod
    def calculate_utilization(
        bps: Optional[int],
        speed_bps: Optional[int]
    ) -> Optional[int]:
        """
        Calculate utilization percentage.
        
        Args:
            bps: Current traffic rate in bits per second
            speed_bps: Interface speed in bits per second
            
        Returns:
            Utilization percentage (0-100), None if cannot calculate
        """
        if bps is None or speed_bps is None or speed_bps <= 0:
            return None
        
        utilization = int((bps / speed_bps) * 100)
        
        # Clamp to 0-100 range
        return max(0, min(100, utilization))
    
    @staticmethod
    def calculate_interface_metrics(
        current_rx_bytes: int,
        current_tx_bytes: int,
        previous_rx_bytes: Optional[int],
        previous_tx_bytes: Optional[int],
        current_time: datetime,
        previous_time: Optional[datetime],
        speed_bps: Optional[int]
    ) -> dict:
        """
        Calculate complete interface metrics from counters.
        
        Returns:
            Dictionary with:
            - rx_bps: Receive rate (bits/sec) or None
            - tx_bps: Transmit rate (bits/sec) or None
            - utilization_in: Inbound utilization (%) or None
            - utilization_out: Outbound utilization (%) or None
            - is_counter_reset: True if counter reset detected
        """
        # Calculate traffic rates
        rx_bps, rx_reset = TrafficCalculator.calculate_traffic_rate(
            current_rx_bytes, previous_rx_bytes, current_time, previous_time
        )
        
        tx_bps, tx_reset = TrafficCalculator.calculate_traffic_rate(
            current_tx_bytes, previous_tx_bytes, current_time, previous_time
        )
        
        # Calculate utilization
        utilization_in = TrafficCalculator.calculate_utilization(rx_bps, speed_bps)
        utilization_out = TrafficCalculator.calculate_utilization(tx_bps, speed_bps)
        
        return {
            'rx_bps': rx_bps,
            'tx_bps': tx_bps,
            'utilization_in': utilization_in,
            'utilization_out': utilization_out,
            'is_counter_reset': rx_reset or tx_reset
        }
