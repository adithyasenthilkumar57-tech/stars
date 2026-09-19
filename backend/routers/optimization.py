"""ClearWay AI — Optimization router"""
from fastapi import APIRouter
from models.optimization import OptimizationRequest, OptimizationMethod
from services.optimization_service import optimization_service
from data.demo_store_state import app_state

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.post("/run")
async def run_optimization(request: OptimizationRequest):
    """Run optimization (classical, adaptive, or hybrid quantum)."""
    from data.demo_seed import demo_store
    demo_store.initialize()
    intersections = demo_store.get_intersections()

    result = optimization_service.run_optimization(request, intersections)
    app_state.latest_optimization = result.model_dump()

    return result.model_dump()


@router.get("/methods")
async def get_methods():
    return {
        "methods": [
            {
                "id": OptimizationMethod.CLASSICAL_FIXED.value,
                "label": "Classical Fixed Timing",
                "description": "Fixed 45s/35s NS/EW green. No adaptation. Baseline only.",
                "icon": "fixed",
            },
            {
                "id": OptimizationMethod.CLASSICAL_ADAPTIVE.value,
                "label": "Rule-Based Adaptive",
                "description": "Greedy timing adjustment based on queue length and congestion score.",
                "icon": "adaptive",
            },
            {
                "id": OptimizationMethod.HYBRID_QUANTUM.value,
                "label": "Hybrid Quantum-Classical (QAOA)",
                "description": "QUBO formulation + QAOA via Qiskit Aer simulator. Always labeled QUANTUM SIMULATOR.",
                "icon": "quantum",
                "badge": "QUANTUM SIMULATOR",
            },
        ]
    }
