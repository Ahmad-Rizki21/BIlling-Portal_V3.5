import asyncio
import logging
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple, Union

import routeros_api

logger = logging.getLogger(__name__)


# Circuit Breaker States
class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, no requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5  # Number of failures before tripping
    recovery_timeout: int = 60  # Seconds to wait before trying again
    expected_exception: tuple = (Exception,)  # Exceptions that count as failures


@dataclass
class ConnectionMetrics:
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    retry_attempts: int = 0
    circuit_breaker_trips: int = 0


class MikrotikConnectionPool:
    def __init__(self, max_connections: int = 10, timeout: int = 30, idle_timeout: int = 300) -> None:
        self.max_connections = max_connections
        self.timeout = timeout  # Timeout for API calls
        self.idle_timeout = idle_timeout  # Time after which idle connections are closed
        self.connections: Dict[str, OrderedDict] = {}  # Server host -> connections pool
        self.lock = threading.Lock()
        self.active_connections: Dict[str, Dict[str, Any]] = {}  # Track active connections by connection object

        # Circuit Breaker per server
        self.circuit_states: Dict[str, CircuitState] = {}
        self.circuit_failures: Dict[str, int] = {}
        self.circuit_last_failure: Dict[str, float] = {}
        self.circuit_config = CircuitBreakerConfig()

        # Connection metrics
        self.metrics = ConnectionMetrics()

        # Connection health monitoring
        self.connection_health: Dict[str, Dict[str, Any]] = {}
        self.last_health_check: Dict[str, float] = {}

    def _get_pool_key(self, host_ip: str, port: int) -> str:
        """Generate a unique key for each Mikrotik server connection."""
        return f"{host_ip}:{port}"

    def _initialize_circuit_breaker(self, pool_key: str) -> None:
        """Initialize circuit breaker for a server if not exists."""
        if pool_key not in self.circuit_states:
            self.circuit_states[pool_key] = CircuitState.CLOSED
            self.circuit_failures[pool_key] = 0
            self.circuit_last_failure[pool_key] = 0.0
            self.connection_health[pool_key] = {
                "healthy": True,
                "last_check": 0.0,
                "consecutive_failures": 0,
                "total_requests": 0,
                "successful_requests": 0,
            }

    def _check_circuit_breaker(self, pool_key: str) -> bool:
        """Check if circuit breaker allows request to proceed."""
        self._initialize_circuit_breaker(pool_key)

        current_time = time.time()
        state = self.circuit_states[pool_key]

        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if current_time - self.circuit_last_failure[pool_key] > self.circuit_config.recovery_timeout:
                logger.info(f"Circuit breaker for {pool_key} moving to HALF_OPEN")
                self.circuit_states[pool_key] = CircuitState.HALF_OPEN
                self.circuit_failures[pool_key] = 0
                return True
            return False
        else:  # CircuitState.HALF_OPEN
            # Allow one request to test if service recovered
            return True

    def _record_success(self, pool_key: str) -> None:
        """Record successful connection and reset circuit breaker."""
        self._initialize_circuit_breaker(pool_key)

        if self.circuit_states[pool_key] == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker for {pool_key} reset to CLOSED after successful request")
            self.circuit_states[pool_key] = CircuitState.CLOSED

        self.circuit_failures[pool_key] = 0
        self.circuit_last_failure[pool_key] = 0.0

        # Update health metrics
        health = self.connection_health[pool_key]
        health["healthy"] = True
        health["consecutive_failures"] = 0
        health["successful_requests"] += 1

    def _record_failure(self, pool_key: str, error: Exception) -> None:
        """Record failed connection and potentially trip circuit breaker."""
        self._initialize_circuit_breaker(pool_key)

        # Only count expected exceptions
        if isinstance(error, self.circuit_config.expected_exception):
            self.circuit_failures[pool_key] += 1
            self.circuit_last_failure[pool_key] = time.time()

            # Update health metrics
            health = self.connection_health[pool_key]
            health["healthy"] = False
            health["consecutive_failures"] += 1
            self.metrics.failed_connections += 1

            logger.warning(f"Connection failure recorded for {pool_key}: {error}")
            logger.warning(f"Consecutive failures: {health['consecutive_failures']}")

            # Check if we should trip the circuit breaker
            state = self.circuit_states[pool_key]
            if state == CircuitState.CLOSED and self.circuit_failures[pool_key] >= self.circuit_config.failure_threshold:

                logger.error(f"CIRCUIT BREAKER TRIPPED for {pool_key}!")
                self.circuit_states[pool_key] = CircuitState.OPEN
                self.metrics.circuit_breaker_trips += 1

            elif state == CircuitState.HALF_OPEN:
                # Immediate trip on failure in half-open state
                logger.error(f"Circuit breaker for {pool_key} re-tripped to OPEN")
                self.circuit_states[pool_key] = CircuitState.OPEN
                self.circuit_last_failure[pool_key] = time.time()

    def _get_connection(self, host_ip: str, port: int, username: str, password: str) -> Tuple[Any, Any]:
        """Create a new Mikrotik API connection."""
        try:
            connection = routeros_api.RouterOsApiPool(
                host_ip, username=username, password=password, port=port, plaintext_login=True
            )
            api = connection.get_api()

            # Store connection metadata
            pool_key = self._get_pool_key(host_ip, port)
            connection_info = {
                "connection": connection,
                "api": api,
                "created_at": time.time(),
                "last_used": time.time(),
                "host": host_ip,
                "port": port,
            }

            # Track as active connection
            self.active_connections[str(id(connection))] = connection_info  # type: ignore

            return api, connection
        except Exception as e:
            logger.error(f"Failed to create connection to {host_ip}:{port}: {e}")
            raise e

    def get_connection(self, host_ip: str, port: int, username: str, password: str) -> Tuple[Any, Any]:
        """Get an available connection from the pool or create a new one."""
        pool_key = self._get_pool_key(host_ip, port)

        # Check circuit breaker first
        if not self._check_circuit_breaker(pool_key):
            logger.error(f"Circuit breaker OPEN for {pool_key}, connection rejected")
            raise ConnectionError(f"Service unavailable for {pool_key} - circuit breaker open")

        with self.lock:
            # Update metrics
            self.metrics.total_connections += 1
            health = self.connection_health.get(pool_key, {})
            health["total_requests"] = health.get("total_requests", 0) + 1

            # Check if we have a connection pool for this server
            if pool_key not in self.connections:
                self.connections[pool_key] = OrderedDict()

            # Find an idle connection
            pool = self.connections[pool_key]

            # Clean up expired connections with proper leak prevention
            current_time = time.time()
            to_remove = []
            for conn_key, conn_info in list(pool.items()):
                if current_time - conn_info["last_used"] > self.idle_timeout:
                    to_remove.append(conn_key)
                    logger.warning(
                        f"Connection {conn_key} to {pool_key} expired ({current_time - conn_info['last_used']:.1f}s > {self.idle_timeout}s)"
                    )

            # Remove expired connections with proper cleanup
            for conn_key in to_remove:
                if conn_key in pool:
                    conn_info = pool.pop(conn_key)
                    try:
                        conn_info["connection"].disconnect()
                        logger.info(f"Cleaned up expired connection to {pool_key}")
                    except Exception as e:
                        logger.error(f"Error disconnecting expired connection {conn_key}: {e}")
                    # Remove from active connections tracking
                    conn_id = str(id(conn_info["connection"]))
                    if conn_id in self.active_connections:
                        del self.active_connections[conn_id]  # type: ignore

            # Try to reuse an existing connection (with health check)
            if pool:
                # Get the most recently used connection
                conn_key, conn_info = pool.popitem(last=False)  # FIFO

                # Quick health check - test if connection is still alive
                try:
                    # Simple test command to check connection health
                    test_result = conn_info["api"].get_resource("/system/identity").get()
                    if test_result:
                        pool[conn_key] = conn_info  # Put it back at the end (most recently used)
                        conn_info["last_used"] = current_time
                        logger.info(f"Reusing healthy connection to {pool_key}")
                        self._record_success(pool_key)
                        return conn_info["api"], conn_info["connection"]
                    else:
                        # Connection seems dead, remove it
                        logger.warning(f"Dead connection detected for {pool_key}, removing")
                        try:
                            conn_info["connection"].disconnect()
                        except:
                            pass
                        conn_id = str(id(conn_info["connection"]))
                        if conn_id in self.active_connections:
                            del self.active_connections[conn_id]  # type: ignore
                except Exception as e:
                    # Connection is unhealthy
                    logger.warning(f"Unhealthy connection for {pool_key}: {e}")
                    try:
                        conn_info["connection"].disconnect()
                    except:
                        pass
                    conn_id = str(id(conn_info["connection"]))
                    if conn_id in self.active_connections:
                        del self.active_connections[conn_id]  # type: ignore
                    self._record_failure(pool_key, e)

            # Create new connection if pool is not full
            if len(pool) < self.max_connections:
                try:
                    api, connection = self._get_connection(host_ip, port, username, password)

                    # Add to pool
                    conn_key = f"{host_ip}:{port}:{len(pool)}"  # Unique connection key
                    conn_info = {
                        "connection": connection,
                        "api": api,
                        "created_at": current_time,
                        "last_used": current_time,
                        "host": host_ip,
                        "port": port,
                        "pool_key": pool_key,
                    }
                    pool[conn_key] = conn_info

                    logger.info(f"Created new connection to {pool_key}")
                    self._record_success(pool_key)
                    self.metrics.active_connections += 1
                    return api, connection

                except Exception as e:
                    self._record_failure(pool_key, e)
                    raise e
            else:
                # If pool is full, create a temporary connection (not in pool)
                logger.warning(f"Connection pool full for {pool_key}, creating temporary connection")
                try:
                    api, connection = self._get_connection(host_ip, port, username, password)
                    self._record_success(pool_key)
                    self.metrics.active_connections += 1
                    return api, connection
                except Exception as e:
                    self._record_failure(pool_key, e)
                    raise e

    def return_connection(self, connection: Any, host_ip: str, port: int) -> None:
        """Return a connection to the pool for reuse."""
        pool_key = self._get_pool_key(host_ip, port)

        with self.lock:
            # Decrease active connection count
            self.metrics.active_connections = max(0, self.metrics.active_connections - 1)

            if pool_key in self.connections:
                pool = self.connections[pool_key]

                # Check if this connection is already in the pool
                conn_key = None
                for key, conn_info in pool.items():
                    if conn_info["connection"] is connection:
                        conn_key = key
                        break

                # If it's a pooled connection, update its usage time
                if conn_key:
                    pool[conn_key]["last_used"] = time.time()
                    # Move to the end (most recently used)
                    pool.move_to_end(conn_key, last=True)
                    logger.info(f"Returned connection to pool for {pool_key}")

                # If it's a temporary connection, close it properly
                else:
                    try:
                        connection.disconnect()
                        logger.info(f"Closed temporary connection to {pool_key}")
                        # Remove from active connections tracking
                        conn_id = str(id(connection))  # type: ignore
                        if conn_id in self.active_connections:
                            del self.active_connections[conn_id]
                    except Exception as e:
                        logger.error(f"Error closing temporary connection to {pool_key}: {e}")
                        # Force cleanup even on error
                        conn_id = str(id(connection))  # type: ignore
                        if conn_id in self.active_connections:
                            del self.active_connections[conn_id]
            else:
                # If pool doesn't exist for this server, just close the connection properly
                try:
                    connection.disconnect()
                    logger.info(f"Closed connection to {pool_key}")
                    # Remove from active connections tracking
                    conn_id = str(id(connection))  # type: ignore
                    if conn_id in self.active_connections:
                        del self.active_connections[conn_id]
                except Exception as e:
                    logger.error(f"Error closing connection to {pool_key}: {e}")
                    # Force cleanup even on error
                    conn_id = str(id(connection))  # type: ignore
                    if conn_id in self.active_connections:
                        del self.active_connections[conn_id]

    def close_all_connections(self) -> None:
        """Close all connections in the pool with proper cleanup."""
        with self.lock:
            total_cleaned = 0
            for pool_key, pool in self.connections.items():
                logger.info(f"Cleaning up connections for {pool_key}")
                connections_to_clean = list(pool.items())
                for conn_key, conn_info in connections_to_clean:
                    try:
                        conn_info["connection"].disconnect()
                        logger.info(f"Closed pooled connection {conn_key} to {pool_key}")
                        total_cleaned += 1
                        # Remove from active connections tracking
                        conn_id = str(id(conn_info["connection"]))
                        if conn_id in self.active_connections:
                            del self.active_connections[conn_id]
                    except Exception as e:
                        logger.error(f"Error closing connection {conn_key} to {pool_key}: {e}")
                        # Force cleanup even on error
                        conn_id = str(id(conn_info["connection"]))
                        if conn_id in self.active_connections:
                            del self.active_connections[conn_id]

            # Clear all pools
            self.connections.clear()

            # Clean up any remaining active connections (safety net)
            remaining_connections = list(self.active_connections.items())
            for conn_id, conn_info in remaining_connections:
                try:
                    conn_info["connection"].disconnect()
                    logger.info(f"Force cleaned remaining connection {conn_id}")
                    total_cleaned += 1
                except Exception as e:
                    logger.error(f"Error force cleaning connection {conn_id}: {e}")
                finally:
                    if conn_id in self.active_connections:
                        del self.active_connections[conn_id]

            # Reset metrics
            self.metrics.active_connections = 0

            logger.info(f"Connection cleanup complete. Cleaned {total_cleaned} connections.")

    @contextmanager
    def connection_context(self, host_ip: str, port: int, username: str, password: str):
        """Context manager to handle connection lifecycle automatically."""
        api, connection = None, None
        try:
            api, connection = self.get_connection(host_ip, port, username, password)
            yield api, connection
        finally:
            if connection:
                self.return_connection(connection, host_ip, port)

    def execute_with_retry(
        self,
        host_ip: str,
        port: int,
        username: str,
        password: str,
        operation_func: Callable[[Any], Any],
        max_retries: int = 3,
        retry_delay: int = 1
    ) -> Any:
        """Execute an operation with enhanced retry mechanism and circuit breaker integration."""
        pool_key = self._get_pool_key(host_ip, port)
        last_error: Union[Exception, None] = None

        # Initialize circuit breaker for this server
        self._initialize_circuit_breaker(pool_key)

        for attempt in range(max_retries):
            api, connection = None, None
            connection_established = False

            try:
                # Check circuit breaker before each attempt
                if not self._check_circuit_breaker(pool_key):
                    error_msg = f"Circuit breaker OPEN for {pool_key} on attempt {attempt + 1}"
                    logger.error(error_msg)
                    raise ConnectionError(error_msg)

                logger.info(f"Attempt {attempt + 1}/{max_retries} for {host_ip}:{port}")

                # Get connection with built-in circuit breaker check
                api, connection = self.get_connection(host_ip, port, username, password)
                connection_established = True

                # Track retry attempts for metrics
                if attempt > 0:
                    self.metrics.retry_attempts += 1

                # Execute the operation
                result = operation_func(api)

                # Record success and return result
                self._record_success(pool_key)
                logger.info(f"Operation successful for {pool_key} on attempt {attempt + 1}")
                return result

            except ConnectionError as ce:
                # Circuit breaker related error - don't retry
                logger.error(f"Circuit breaker error for {pool_key}: {ce}")
                last_error = ce
                break  # Exit retry loop immediately

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for {pool_key}: {type(e).__name__}: {e}")

                # Record failure for circuit breaker
                self._record_failure(pool_key, e)

                # Proper connection cleanup
                if connection and connection_established:
                    try:
                        self.return_connection(connection, host_ip, port)
                    except Exception as cleanup_error:
                        logger.error(f"Error returning connection to pool: {cleanup_error}")
                elif connection:
                    # Connection was established but not properly returned - force cleanup
                    try:
                        connection.disconnect()
                        logger.info(f"Force disconnected failed connection to {pool_key}")
                        # Remove from active connections tracking
                        conn_id = str(id(connection))  # type: ignore
                        if conn_id in self.active_connections:
                            del self.active_connections[conn_id]
                    except Exception as cleanup_error:
                        logger.error(f"Error force disconnecting connection: {cleanup_error}")

                # Check if we should retry
                if attempt < max_retries - 1:
                    # Use exponential backoff with jitter to prevent thundering herd
                    base_delay = retry_delay * (2**attempt)  # Exponential: 1, 2, 4, 8...
                    jitter = base_delay * 0.1  # Add 10% jitter
                    actual_delay = base_delay + jitter

                    logger.info(f"Waiting {actual_delay:.2f}s before retry {attempt + 2}")
                    time.sleep(actual_delay)
                else:
                    logger.error(f"Max retries ({max_retries}) exhausted for {pool_key}")

        # If we get here, all retries failed
        logger.error(f"All {max_retries} attempts failed for {pool_key}. Final error: {last_error}")

        # Check if we need to force circuit breaker trip
        circuit_state = self.circuit_states.get(pool_key, CircuitState.CLOSED)
        if circuit_state != CircuitState.OPEN:
            logger.warning(f"Forcing circuit breaker to OPEN for {pool_key} after retry exhaustion")
            self.circuit_states[pool_key] = CircuitState.OPEN
            self.circuit_last_failure[pool_key] = time.time()
            self.metrics.circuit_breaker_trips += 1

        raise last_error or Exception(f"Unknown error occurred for {pool_key}")

    def get_connection_health_status(self, host_ip: str, port: int) -> Dict[str, Any]:
        """Get detailed health status for a specific server connection."""
        pool_key = self._get_pool_key(host_ip, port)
        self._initialize_circuit_breaker(pool_key)

        current_time = time.time()
        health = self.connection_health[pool_key]
        circuit_state = self.circuit_states[pool_key]

        # Calculate health metrics
        success_rate = 0.0
        if health["total_requests"] > 0:
            success_rate = (health["successful_requests"] / health["total_requests"]) * 100

        # Determine overall health status
        if circuit_state == CircuitState.OPEN:
            status = "CRITICAL"
            status_message = "Circuit breaker OPEN - service unavailable"
        elif circuit_state == CircuitState.HALF_OPEN:
            status = "WARNING"
            status_message = "Circuit breaker HALF_OPEN - testing service recovery"
        elif health["consecutive_failures"] > 3:
            status = "DEGRADED"
            status_message = f"Multiple consecutive failures ({health['consecutive_failures']})"
        elif success_rate < 80.0:
            status = "DEGRADED"
            status_message = f"Low success rate ({success_rate:.1f}%)"
        else:
            status = "HEALTHY"
            status_message = "All systems operational"

        # Get pool statistics
        pool_stats = {}
        if pool_key in self.connections:
            pool = self.connections[pool_key]
            pool_stats = {
                "pool_size": len(pool),
                "max_connections": self.max_connections,
                "pool_utilization": f"{(len(pool) / self.max_connections) * 100:.1f}%",
                "expired_connections": len(
                    [conn for conn in pool.values() if current_time - conn["last_used"] > self.idle_timeout]
                ),
            }

        return {
            "server": f"{host_ip}:{port}",
            "status": status,
            "status_message": status_message,
            "circuit_breaker": {
                "state": circuit_state.value,
                "failures": self.circuit_failures[pool_key],
                "last_failure": self.circuit_last_failure[pool_key],
                "threshold": self.circuit_config.failure_threshold,
                "recovery_timeout": self.circuit_config.recovery_timeout,
            },
            "health_metrics": {
                "total_requests": health["total_requests"],
                "successful_requests": health["successful_requests"],
                "success_rate": f"{success_rate:.1f}%",
                "consecutive_failures": health["consecutive_failures"],
                "last_check": health["last_check"],
            },
            "pool_statistics": pool_stats,
            "timestamp": current_time,
        }

    def get_all_servers_health(self) -> Dict[str, Any]:
        """Get health status for all Mikrotik servers."""
        current_time = time.time()

        # Collect health for all known servers
        servers_health = {}
        for pool_key in self.connections.keys():
            # Extract host and port from pool_key
            try:
                host_ip, port = pool_key.split(":")
                port = int(port)
                servers_health[pool_key] = self.get_connection_health_status(host_ip, port)
            except ValueError:
                logger.error(f"Invalid pool key format: {pool_key}")

        # Get overall system metrics
        total_active = len(self.active_connections)
        total_pooled = sum(len(pool) for pool in self.connections.values())

        return {
            "summary": {
                "total_servers": len(servers_health),
                "healthy_servers": len([h for h in servers_health.values() if h["status"] == "HEALTHY"]),
                "degraded_servers": len([h for h in servers_health.values() if h["status"] == "DEGRADED"]),
                "critical_servers": len([h for h in servers_health.values() if h["status"] in ["WARNING", "CRITICAL"]]),
                "total_active_connections": total_active,
                "total_pooled_connections": total_pooled,
                "timestamp": current_time,
            },
            "servers": servers_health,
            "system_metrics": {
                "total_connections": self.metrics.total_connections,
                "failed_connections": self.metrics.failed_connections,
                "retry_attempts": self.metrics.retry_attempts,
                "circuit_breaker_trips": self.metrics.circuit_breaker_trips,
                "active_connections": self.metrics.active_connections,
            },
        }

    def cleanup_stale_connections(self) -> Dict[str, int]:
        """Clean up stale connections and return cleanup statistics."""
        current_time = time.time()
        cleanup_stats = {"expired_connections": 0, "unhealthy_connections": 0, "orphaned_connections": 0, "total_cleaned": 0}

        with self.lock:
            for pool_key, pool in list(self.connections.items()):
                connections_to_remove = []

                for conn_key, conn_info in list(pool.items()):
                    should_remove = False
                    remove_reason = ""

                    # Check for expired connections
                    if current_time - conn_info["last_used"] > self.idle_timeout:
                        should_remove = True
                        remove_reason = "expired"
                        cleanup_stats["expired_connections"] += 1

                    # Check for unhealthy connections (test connection)
                    if not should_remove:
                        try:
                            # Quick health check
                            test_result = conn_info["api"].get_resource("/system/identity").get()
                            if not test_result:
                                should_remove = True
                                remove_reason = "unhealthy"
                                cleanup_stats["unhealthy_connections"] += 1
                        except Exception:
                            should_remove = True
                            remove_reason = "unhealthy"
                            cleanup_stats["unhealthy_connections"] += 1

                    # Remove the connection if needed
                    if should_remove:
                        connections_to_remove.append((conn_key, conn_info, remove_reason))
                        cleanup_stats["total_cleaned"] += 1

                # Actually remove the connections
                for conn_key, conn_info, reason in connections_to_remove:
                    if conn_key in pool:
                        pool.pop(conn_key)
                        try:
                            conn_info["connection"].disconnect()
                            logger.info(f"Cleaned up {reason} connection {conn_key} from {pool_key}")
                        except Exception as e:
                            logger.error(f"Error disconnecting {reason} connection {conn_key}: {e}")
                        finally:
                            # Remove from active connections tracking
                            conn_id = str(id(conn_info["connection"]))
                            if conn_id in self.active_connections:
                                del self.active_connections[conn_id]

                # Remove empty pools
                if not pool and pool_key in self.connections:
                    self.connections.pop(pool_key)
                    logger.info(f"Removed empty pool for {pool_key}")

            # Clean up orphaned active connections (safety net)
            orphaned_connections = []
            for conn_id, conn_info in list(self.active_connections.items()):
                # Check if connection is still in any pool
                found_in_pool = False
                for pool in self.connections.values():
                    if any(c_info["connection"] is conn_info["connection"] for c_info in pool.values()):
                        found_in_pool = True
                        break

                if not found_in_pool:
                    orphaned_connections.append((conn_id, conn_info))
                    cleanup_stats["orphaned_connections"] += 1
                    cleanup_stats["total_cleaned"] += 1

            # Clean up orphaned connections
            for conn_id, conn_info in orphaned_connections:
                try:
                    conn_info["connection"].disconnect()
                    logger.info(f"Cleaned up orphaned connection {conn_id}")
                except Exception as e:
                    logger.error(f"Error disconnecting orphaned connection {conn_id}: {e}")
                finally:
                    if conn_id in self.active_connections:
                        del self.active_connections[conn_id]

        logger.info(f"Connection cleanup complete: {cleanup_stats}")
        return cleanup_stats

    def get_pool_config(self) -> Dict[str, Any]:
        """Get current pool configuration."""
        return {
            "max_connections": self.max_connections,
            "timeout": self.timeout,
            "idle_timeout": self.idle_timeout,
            "circuit_breaker": {
                "failure_threshold": self.circuit_config.failure_threshold,
                "recovery_timeout": self.circuit_config.recovery_timeout,
                "expected_exceptions": [exc.__name__ for exc in self.circuit_config.expected_exception],
            },
            "active_servers": list(self.connections.keys()),
        }


# Global connection pool instance
mikrotik_pool = MikrotikConnectionPool(max_connections=10, timeout=30, idle_timeout=300)
