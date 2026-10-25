from fastapi import APIRouter, HTTPException,Query, Request, Response, Depends
from decimal import Decimal
from app.repository import create_vehicle, restock_vehicle, list_vehicles, update_vehicle, delete_vehicle, search_vehicles,purchase_vehicle
from app.schemas import StockChange,VehicleCreate, VehicleResponse
from app.security import get_current_user, require_admin

router = APIRouter(
    prefix="/api/vehicles",
    tags=["Vehicles"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    status_code=201,
    response_model=VehicleResponse,
)
def add_vehicle(vehicle: VehicleCreate, request: Request):
    return create_vehicle(
        database_path=request.app.state.database_path,
        vehicle=vehicle,
    )
@router.get(
    "",
    response_model=list[VehicleResponse],
)
def get_vehicles(request: Request):
    return list_vehicles(
        database_path=request.app.state.database_path,
    )
@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
)
def edit_vehicle(
    vehicle_id: str,
    vehicle: VehicleCreate,
    request: Request,
):
    updated_vehicle = update_vehicle(
        database_path=request.app.state.database_path,
        vehicle_id=vehicle_id,
        vehicle=vehicle,
    )

    if updated_vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    return updated_vehicle
@router.delete(
    "/{vehicle_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def remove_vehicle(vehicle_id: str, request: Request):
    deleted = delete_vehicle(
        database_path=request.app.state.database_path,
        vehicle_id=vehicle_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    return Response(status_code=204)
@router.get(
    "/search",
    response_model=list[VehicleResponse],
)
def find_vehicles(
    request: Request,
    make: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    model: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    category: str | None = Query(
        default=None,
        min_length=1,
        max_length=60,
    ),
    min_price: Decimal | None = Query(
        default=None,
        ge=0,
        max_digits=11,
        decimal_places=2,
        allow_inf_nan=False,
    ),
    max_price: Decimal | None = Query(
        default=None,
        ge=0,
        max_digits=11,
        decimal_places=2,
        allow_inf_nan=False,
    ),
):
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=422,
            detail="Minimum price cannot exceed maximum price",
        )

    return search_vehicles(
        database_path=request.app.state.database_path,
        make=make,
        model=model,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )
@router.post(
    "/{vehicle_id}/purchase",
    response_model=VehicleResponse,
)
def buy_vehicle(
    vehicle_id: str,
    stock_change: StockChange,
    request: Request,
):
    vehicle, error = purchase_vehicle(
        database_path=request.app.state.database_path,
        vehicle_id=vehicle_id,
        quantity=stock_change.quantity,
    )

    if error == "not_found":
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    if error == "insufficient_stock":
        raise HTTPException(
            status_code=409,
            detail="Insufficient stock",
        )

    return vehicle

@router.post(
    "/{vehicle_id}/restock",
    response_model=VehicleResponse,
    dependencies=[Depends(require_admin)]
)
def replenish_vehicle(
    vehicle_id: str,
    stock_change: StockChange,
    request: Request,
):
    vehicle, error = restock_vehicle(
        database_path=request.app.state.database_path,
        vehicle_id=vehicle_id,
        quantity=stock_change.quantity,
    )

    if error == "not_found":
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    if error == "stock_limit_exceeded":
        raise HTTPException(
            status_code=409,
            detail="Stock limit exceeded",
        )

    return vehicle