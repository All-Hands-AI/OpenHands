import pytest
from openhands.llm.metrics import Metrics, Cost


def test_metrics_initialization():
    metrics = Metrics()
    assert metrics.accumulated_cost == 0.0
    assert len(metrics.costs) == 0


def test_add_cost():
    metrics = Metrics()
    metrics.add_cost(0.1)
    assert metrics.accumulated_cost == 0.1
    assert len(metrics.costs) == 1
    assert metrics.costs[0].cost == 0.1


def test_add_negative_cost():
    metrics = Metrics()
    with pytest.raises(ValueError):
        metrics.add_cost(-0.1)


def test_merge_metrics():
    metrics1 = Metrics()
    metrics2 = Metrics()
    
    metrics1.add_cost(0.1)
    metrics2.add_cost(0.2)
    
    metrics1.merge(metrics2)
    assert abs(metrics1.accumulated_cost - 0.3) < 1e-10
    assert len(metrics1.costs) == 2


def test_reset_metrics():
    metrics = Metrics()
    metrics.add_cost(0.1)
    metrics.reset()
    assert metrics.accumulated_cost == 0.0
    assert len(metrics.costs) == 0


def test_get_metrics():
    metrics = Metrics()
    metrics.add_cost(0.1)
    data = metrics.get()
    assert abs(data['accumulated_cost'] - 0.1) < 1e-10
    assert len(data['costs']) == 1
    assert isinstance(data['costs'][0], dict)
    assert abs(data['costs'][0]['cost'] - 0.1) < 1e-10
