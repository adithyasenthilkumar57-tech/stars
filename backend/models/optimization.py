"""ClearWay AI — QUBO Model and Optimization Run models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class OptimizationMethod(str, Enum):
    CLASSICAL_FIXED = "classical_fixed"
    CLASSICAL_ADAPTIVE = "classical_adaptive"
    HYBRID_QUANTUM = "hybrid_quantum"


class QUBOVariable(BaseModel):
    name: str       # e.g., "x_J1_ns"
    junction_id: str
    phase: str      # "ns_green" | "ew_green"
    value: Optional[int] = None  # 0 or 1 after solving
    description: str = ""


class QUBOModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    variables: List[QUBOVariable]
    num_variables: int
    num_constraints: int
    cost_matrix: List[List[float]] = Field(default_factory=list)  # Q matrix
    objective_terms: Dict[str, float] = Field(default_factory=dict)
    constraint_penalty: float = 10.0
    formulation_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QAOAConfig(BaseModel):
    num_layers: int = 2
    simulator: str = "qiskit_aer_statevector"
    shots: int = 1024
    optimization_method: str = "COBYLA"
    max_iterations: int = 100
    is_real_hardware: bool = False  # Always False — always label as simulator


class SignalPlan(BaseModel):
    junction_id: str
    junction_label: str
    ns_green_seconds: int
    ew_green_seconds: int
    phase_order: List[str]
    rationale: str = ""


class OptimizationRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    method: OptimizationMethod
    qubo_model: Optional[QUBOModel] = None
    qaoa_config: Optional[QAOAConfig] = None

    # Before/After costs
    cost_before: float
    cost_after: float
    improvement_pct: float

    # Before/After waiting times
    avg_waiting_before: float  # seconds
    avg_waiting_after: float
    queue_before: float
    queue_after: float

    # Results
    signal_plans: List[SignalPlan] = Field(default_factory=list)
    iteration_count: int = 0
    execution_time_ms: float = 0.0
    converged: bool = True
    simulator_status: str = "QUANTUM_SIMULATOR"  # Always labeled

    # Context
    scenario_id: Optional[str] = None
    triggered_by: str = "user"  # user | auto | emergency
    ai_insight: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = "SIMULATED"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class OptimizationRequest(BaseModel):
    method: OptimizationMethod = OptimizationMethod.HYBRID_QUANTUM
    intersection_ids: Optional[List[str]] = None  # None = all active
    emergency_priority: bool = False
    scenario_id: Optional[str] = None
