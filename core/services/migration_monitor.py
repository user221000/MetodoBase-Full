"""
core/services/migration_monitor.py — Monitoreo de migración de BD.

FASE 8 del plan de consolidación.

Proporciona:
- Métricas en tiempo real de operaciones dual-BD
- Alertas por thresholds configurables
- Dashboard de estado de migración
- Exportación de métricas (Prometheus-compatible)
"""
import json
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Alert Levels ────────────────────────────────────────────────────────────

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alerta de migración."""
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "message": self.message,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
        }


# ── Thresholds ──────────────────────────────────────────────────────────────

@dataclass
class AlertThreshold:
    """Threshold para generar alertas."""
    metric_name: str
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    comparison: str = "gt"  # gt, lt, eq
    
    def check(self, value: float) -> Optional[AlertLevel]:
        """Verifica si el valor excede algún threshold."""
        if self.comparison == "gt":
            if value >= self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value >= self.error_threshold:
                return AlertLevel.ERROR
            elif value >= self.warning_threshold:
                return AlertLevel.WARNING
        elif self.comparison == "lt":
            if value <= self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value <= self.error_threshold:
                return AlertLevel.ERROR
            elif value <= self.warning_threshold:
                return AlertLevel.WARNING
        return None


# ── Default Thresholds ──────────────────────────────────────────────────────

DEFAULT_THRESHOLDS = [
    # Error rate de operaciones
    AlertThreshold(
        metric_name="operation_error_rate",
        warning_threshold=0.01,   # 1%
        error_threshold=0.05,     # 5%
        critical_threshold=0.10,  # 10%
        comparison="gt",
    ),
    # Latencia de operaciones (ms)
    AlertThreshold(
        metric_name="operation_latency_p99",
        warning_threshold=500,
        error_threshold=1000,
        critical_threshold=5000,
        comparison="gt",
    ),
    # Parity mismatches
    AlertThreshold(
        metric_name="parity_mismatch_rate",
        warning_threshold=0.001,  # 0.1%
        error_threshold=0.01,     # 1%
        critical_threshold=0.05,  # 5%
        comparison="gt",
    ),
    # Sync lag (segundos de retraso)
    AlertThreshold(
        metric_name="sync_lag_seconds",
        warning_threshold=60,
        error_threshold=300,
        critical_threshold=900,
        comparison="gt",
    ),
    # Success rate (debe estar ALTO)
    AlertThreshold(
        metric_name="success_rate",
        warning_threshold=0.99,
        error_threshold=0.95,
        critical_threshold=0.90,
        comparison="lt",
    ),
]


# ── Metrics Collector ───────────────────────────────────────────────────────

@dataclass
class MetricPoint:
    """Punto de métrica."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MetricsCollector:
    """Recolector de métricas de migración."""
    
    def __init__(self, retention_minutes: int = 60):
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._retention = timedelta(minutes=retention_minutes)
        self._lock = threading.Lock()
    
    def inc_counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Incrementa un contador."""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Establece un gauge."""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observa valor en histograma."""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            # Limitar tamaño
            if len(self._histograms[key]) > 10000:
                self._histograms[key] = self._histograms[key][-5000:]
    
    def record_operation(
        self,
        operation: str,
        source: str,
        success: bool,
        duration_ms: float,
    ):
        """Registra una operación de BD."""
        labels = {"operation": operation, "source": source}
        
        self.inc_counter("db_operations_total", 1, labels)
        if success:
            self.inc_counter("db_operations_success", 1, labels)
        else:
            self.inc_counter("db_operations_error", 1, labels)
        
        self.observe_histogram("db_operation_duration_ms", duration_ms, labels)
    
    def record_sync_event(self, success: bool, lag_seconds: float = 0):
        """Registra evento de sincronización."""
        self.inc_counter("sync_events_total")
        if success:
            self.inc_counter("sync_events_success")
        else:
            self.inc_counter("sync_events_error")
        
        self.set_gauge("sync_lag_seconds", lag_seconds)
    
    def record_parity_check(self, match: bool):
        """Registra resultado de parity check."""
        self.inc_counter("parity_checks_total")
        if not match:
            self.inc_counter("parity_mismatches")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene todas las métricas actuales."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: self._calc_histogram_stats(v) for k, v in self._histograms.items()},
            }
    
    def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """Obtiene valor de una métrica."""
        key = self._make_key(name, labels)
        with self._lock:
            if key in self._counters:
                return self._counters[key]
            if key in self._gauges:
                return self._gauges[key]
        return None
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _calc_histogram_stats(self, values: List[float]) -> Dict[str, float]:
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_vals = sorted(values)
        count = len(sorted_vals)
        
        def percentile(p: float) -> float:
            idx = int(count * p)
            return sorted_vals[min(idx, count - 1)]
        
        return {
            "count": count,
            "sum": sum(sorted_vals),
            "avg": sum(sorted_vals) / count,
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "p99": percentile(0.99),
        }


# ── Migration Monitor ───────────────────────────────────────────────────────

class MigrationMonitor:
    """
    Monitor central de migración.
    
    Uso:
        monitor = get_migration_monitor()
        
        # Registrar operaciones
        monitor.record_operation("read", "legacy", True, 5.2)
        
        # Obtener estado
        status = monitor.get_status()
        
        # Verificar alertas
        alerts = monitor.check_alerts()
    """
    
    def __init__(self, thresholds: List[AlertThreshold] = None):
        self._metrics = MetricsCollector()
        self._thresholds = thresholds or DEFAULT_THRESHOLDS
        self._alerts: List[Alert] = []
        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._start_time = datetime.now(timezone.utc)
    
    # ── Recording ───────────────────────────────────────────────────────────
    
    def record_operation(
        self,
        operation: str,
        source: str,
        success: bool,
        duration_ms: float,
    ):
        """Registra una operación de BD."""
        self._metrics.record_operation(operation, source, success, duration_ms)
    
    def record_sync(self, success: bool, lag_seconds: float = 0):
        """Registra evento de sincronización."""
        self._metrics.record_sync_event(success, lag_seconds)
    
    def record_parity(self, match: bool):
        """Registra resultado de parity check."""
        self._metrics.record_parity_check(match)
    
    def set_migration_phase(self, phase: int):
        """Establece la fase actual de migración."""
        self._metrics.set_gauge("migration_phase", phase)
    
    # ── Queries ─────────────────────────────────────────────────────────────
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado actual de migración."""
        metrics = self._metrics.get_metrics()
        
        # Calcular rates
        total_ops = sum(
            v for k, v in metrics["counters"].items()
            if "db_operations_total" in k
        )
        error_ops = sum(
            v for k, v in metrics["counters"].items()
            if "db_operations_error" in k
        )
        
        error_rate = error_ops / total_ops if total_ops > 0 else 0
        
        # Parity
        parity_total = metrics["counters"].get("parity_checks_total", 0)
        parity_mismatch = metrics["counters"].get("parity_mismatches", 0)
        parity_rate = parity_mismatch / parity_total if parity_total > 0 else 0
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": (datetime.now(timezone.utc) - self._start_time).total_seconds(),
            "migration_phase": metrics["gauges"].get("migration_phase", 1),
            "operations": {
                "total": total_ops,
                "errors": error_ops,
                "error_rate": error_rate,
            },
            "sync": {
                "lag_seconds": metrics["gauges"].get("sync_lag_seconds", 0),
                "events_total": metrics["counters"].get("sync_events_total", 0),
                "events_error": metrics["counters"].get("sync_events_error", 0),
            },
            "parity": {
                "checks_total": parity_total,
                "mismatches": parity_mismatch,
                "mismatch_rate": parity_rate,
            },
            "latency": self._get_latency_stats(metrics),
            "active_alerts": len([a for a in self._alerts if not a.acknowledged]),
        }
    
    def _get_latency_stats(self, metrics: Dict) -> Dict[str, Any]:
        """Extrae stats de latencia."""
        for key, stats in metrics.get("histograms", {}).items():
            if "duration_ms" in key:
                return stats
        return {}
    
    # ── Alerts ──────────────────────────────────────────────────────────────
    
    def check_alerts(self) -> List[Alert]:
        """Verifica thresholds y genera alertas."""
        status = self.get_status()
        new_alerts = []
        
        # Mapear métricas derivadas
        metric_values = {
            "operation_error_rate": status["operations"]["error_rate"],
            "parity_mismatch_rate": status["parity"]["mismatch_rate"],
            "sync_lag_seconds": status["sync"]["lag_seconds"],
            "success_rate": 1 - status["operations"]["error_rate"],
        }
        
        latency = status.get("latency", {})
        if latency:
            metric_values["operation_latency_p99"] = latency.get("p99", 0)
        
        # Verificar thresholds
        for threshold in self._thresholds:
            value = metric_values.get(threshold.metric_name)
            if value is None:
                continue
            
            level = threshold.check(value)
            if level:
                alert = Alert(
                    level=level,
                    message=f"{threshold.metric_name} = {value:.4f} exceeds threshold",
                    metric_name=threshold.metric_name,
                    current_value=value,
                    threshold=getattr(threshold, f"{level.value}_threshold"),
                )
                new_alerts.append(alert)
                self._alerts.append(alert)
                
                # Notificar handlers
                for handler in self._alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error("Alert handler failed: %s", e)
        
        return new_alerts
    
    def get_alerts(self, include_acknowledged: bool = False) -> List[Alert]:
        """Obtiene alertas."""
        if include_acknowledged:
            return list(self._alerts)
        return [a for a in self._alerts if not a.acknowledged]
    
    def acknowledge_alert(self, index: int) -> bool:
        """Reconoce una alerta."""
        if 0 <= index < len(self._alerts):
            self._alerts[index].acknowledged = True
            return True
        return False
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Añade handler para alertas."""
        self._alert_handlers.append(handler)
    
    # ── Export ──────────────────────────────────────────────────────────────
    
    def export_prometheus(self) -> str:
        """Exporta métricas en formato Prometheus."""
        lines = []
        metrics = self._metrics.get_metrics()
        
        # Counters
        for key, value in metrics["counters"].items():
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in metrics["gauges"].items():
            lines.append(f"{key} {value}")
        
        # Histograms (simplificado)
        for key, stats in metrics["histograms"].items():
            base_name = key.split("{")[0]
            lines.append(f"{base_name}_count {stats['count']}")
            lines.append(f"{base_name}_sum {stats['sum']}")
            lines.append(f'{base_name}{{quantile="0.5"}} {stats["p50"]}')
            lines.append(f'{base_name}{{quantile="0.95"}} {stats["p95"]}')
            lines.append(f'{base_name}{{quantile="0.99"}} {stats["p99"]}')
        
        return "\n".join(lines)
    
    def export_json(self) -> str:
        """Exporta estado completo como JSON."""
        return json.dumps({
            "status": self.get_status(),
            "alerts": [a.to_dict() for a in self.get_alerts()],
            "metrics": self._metrics.get_metrics(),
        }, indent=2)


# ── Singleton ───────────────────────────────────────────────────────────────

_monitor: Optional[MigrationMonitor] = None


def get_migration_monitor() -> MigrationMonitor:
    """Obtiene el monitor singleton."""
    global _monitor
    if _monitor is None:
        _monitor = MigrationMonitor()
    return _monitor
