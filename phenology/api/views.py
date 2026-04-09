import uuid
import logging
from datetime import date
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import (
    Farm, Location, Block, Flight, Image, KPI, Action,
    Prediction, PhenologyStage, ActionType, ChemicalType
)

logger = logging.getLogger(__name__)


def _coerce_date(value):
    """Parse request date values (ISO YYYY-MM-DD strings) for DateField writes."""
    if value is None or value == '':
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def success_response(data, status_code=200):
    """Helper function for success responses."""
    return Response({
        'success': True,
        'data': data
    }, status=status_code)


def failure_response(message, status_code=400):
    """Helper function for error responses."""
    return Response({
        'success': False,
        'error': message
    }, status=status_code)


def get_user_id(request):
    """Extract user ID from request."""
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


# ==================== HEALTH CHECK ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({'status': 'ok', 'service': 'phenology'})


# ==================== AUTH (simple token, same pattern as Data-Collection) ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Create a Django user and return an API token.

    POST /api/auth/register/
    Body: { "email": "...", "password": "...", "username": "<optional>" }
    """
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password')
    username = (request.data.get('username') or '').strip() or email

    if not email:
        return failure_response('email is required')
    if not password:
        return failure_response('password is required')
    if User.objects.filter(email__iexact=email).exists():
        return failure_response('A user with this email already exists')
    if User.objects.filter(username=username).exists():
        return failure_response('A user with this username already exists')

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    token, _ = Token.objects.get_or_create(user=user)
    return success_response({
        'token': token.key,
        'user_id': user.id,
        'email': user.email,
        'username': user.username,
    }, status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Obtain an API token (lookup user by email, same as Data-Collection).

    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    """
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password')

    if not email or not password:
        return failure_response('email and password are required')

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return failure_response('Invalid credentials', status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=user.username, password=password)
    if not user:
        return failure_response('Invalid credentials', status.HTTP_400_BAD_REQUEST)

    token, _ = Token.objects.get_or_create(user=user)
    return success_response({'token': token.key})


# ==================== FARM ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_farm(request):
    """
    Create a new farm.

    POST /api/farms/
    Request Body:
    {
        "name": "Farm Name",
        "organic_certified": false,
        "locations": [{"latitude": 12.345, "longitude": 67.890}]
    }
    """
    name = request.data.get('name')
    organic_certified = request.data.get('organic_certified', False)
    locations = request.data.get('locations', [])

    if not name:
        return failure_response('name is required')

    farm = Farm.objects.create(
        name=name,
        organic_certified=organic_certified,
        created_by=request.user,
        updated_by=request.user
    )

    # Create locations
    for loc_data in locations:
        Location.objects.create(
            farm=farm,
            latitude=loc_data.get('latitude'),
            longitude=loc_data.get('longitude')
        )

    return success_response({
        'id': str(farm.id),
        'name': farm.name,
        'organic_certified': farm.organic_certified,
        'created_at': farm.created_at.isoformat()
    }, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_farms(request):
    """
    List all farms with optional filters.

    GET /api/farms/
    Query params:
    - organic: Filter by organic certification (true/false)
    - search: Search by name
    """
    queryset = Farm.objects.prefetch_related('locations').all()

    organic = request.query_params.get('organic')
    if organic:
        queryset = queryset.filter(organic_certified=organic.lower() == 'true')

    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(name__icontains=search)

    farms = [
        {
            'id': str(f.id),
            'name': f.name,
            'organic_certified': f.organic_certified,
            'locations': [
                {'latitude': float(loc.latitude), 'longitude': float(loc.longitude)}
                for loc in f.locations.all()
            ],
            'blocks_count': f.blocks.count(),
            'created_at': f.created_at.isoformat()
        }
        for f in queryset
    ]

    return success_response({'farms': farms, 'total': len(farms)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_farm(request, farm_id):
    """Get a single farm by ID."""
    try:
        farm = Farm.objects.prefetch_related('locations', 'blocks').get(id=farm_id)
    except Farm.DoesNotExist:
        return failure_response('Farm not found', 404)

    return success_response({
        'id': str(farm.id),
        'name': farm.name,
        'organic_certified': farm.organic_certified,
        'locations': [
            {'id': str(loc.id), 'latitude': float(loc.latitude), 'longitude': float(loc.longitude)}
            for loc in farm.locations.all()
        ],
        'blocks': [
            {'id': str(b.id), 'name': b.name, 'variety': b.variety}
            for b in farm.blocks.all()
        ],
        'created_at': farm.created_at.isoformat(),
        'updated_at': farm.updated_at.isoformat()
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_farm(request, farm_id):
    """Update a farm."""
    try:
        farm = Farm.objects.get(id=farm_id)
    except Farm.DoesNotExist:
        return failure_response('Farm not found', 404)

    if request.data.get('name'):
        farm.name = request.data['name']
    if 'organic_certified' in request.data:
        farm.organic_certified = request.data['organic_certified']
    farm.updated_by = request.user
    farm.save()

    return success_response({
        'id': str(farm.id),
        'name': farm.name,
        'organic_certified': farm.organic_certified
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_farm(request, farm_id):
    """Delete a farm (cascade deletes all blocks)."""
    try:
        farm = Farm.objects.get(id=farm_id)
        farm.delete()
        return success_response({'message': 'Farm deleted successfully'})
    except Farm.DoesNotExist:
        return failure_response('Farm not found', 404)


# ==================== BLOCK ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_block(request):
    """
    Create a new block within a farm.

    POST /api/blocks/
    Request Body:
    {
        "farm_id": "uuid",
        "variety": "Cabernet Sauvignon",
        "name": "Block A",
        "other_language_name": "Block A (Spanish)",
        "locations": [{"latitude": 12.345, "longitude": 67.890}]
    }
    """
    farm_id = request.data.get('farm_id')
    variety = request.data.get('variety')
    name = request.data.get('name')
    other_language_name = request.data.get('other_language_name', '')
    locations = request.data.get('locations', [])

    if not farm_id:
        return failure_response('farm_id is required')
    if not variety:
        return failure_response('variety is required')
    if not name:
        return failure_response('name is required')

    try:
        farm = Farm.objects.get(id=farm_id)
    except Farm.DoesNotExist:
        return failure_response('Farm not found', 404)

    block = Block.objects.create(
        farm=farm,
        variety=variety,
        name=name,
        other_language_name=other_language_name
    )

    # Create locations
    for loc_data in locations:
        Location.objects.create(
            block=block,
            latitude=loc_data.get('latitude'),
            longitude=loc_data.get('longitude')
        )

    return success_response({
        'id': str(block.id),
        'farm_id': str(farm.id),
        'variety': block.variety,
        'name': block.name
    }, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_blocks(request):
    """
    List blocks with filters.

    GET /api/blocks/
    Query params:
    - farm_id: Filter by farm
    - variety: Filter by variety
    """
    queryset = Block.objects.select_related('farm').prefetch_related('locations').all()

    farm_id = request.query_params.get('farm_id')
    if farm_id:
        queryset = queryset.filter(farm_id=farm_id)

    variety = request.query_params.get('variety')
    if variety:
        queryset = queryset.filter(variety__icontains=variety)

    blocks = [
        {
            'id': str(b.id),
            'farm_id': str(b.farm.id),
            'farm_name': b.farm.name,
            'variety': b.variety,
            'name': b.name,
            'other_language_name': b.other_language_name,
            'locations': [
                {'latitude': float(loc.latitude), 'longitude': float(loc.longitude)}
                for loc in b.locations.all()
            ]
        }
        for b in queryset
    ]

    return success_response({'blocks': blocks, 'total': len(blocks)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_block(request, block_id):
    """Get a single block with related data summary."""
    try:
        block = Block.objects.select_related('farm').prefetch_related('locations').get(id=block_id)
    except Block.DoesNotExist:
        return failure_response('Block not found', 404)

    return success_response({
        'id': str(block.id),
        'farm': {
            'id': str(block.farm.id),
            'name': block.farm.name
        },
        'variety': block.variety,
        'name': block.name,
        'other_language_name': block.other_language_name,
        'locations': [
            {'id': str(loc.id), 'latitude': float(loc.latitude), 'longitude': float(loc.longitude)}
            for loc in block.locations.all()
        ],
        'flights_count': block.flights.count(),
        'latest_flight': block.flights.first().flight_date.isoformat() if block.flights.exists() else None
    })


# ==================== FLIGHT ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_flight(request):
    """
    Create a new flight.

    POST /api/flights/
    Request Body:
    {
        "block_id": "uuid",
        "flight_date": "2024-01-15"
    }
    """
    block_id = request.data.get('block_id')
    flight_date = request.data.get('flight_date')

    if not block_id:
        return failure_response('block_id is required')
    if not flight_date:
        return failure_response('flight_date is required')

    flight_date = _coerce_date(flight_date)
    if not flight_date:
        return failure_response('flight_date must be a valid YYYY-MM-DD date')

    try:
        block = Block.objects.get(id=block_id)
    except Block.DoesNotExist:
        return failure_response('Block not found', 404)

    flight = Flight.objects.create(
        block=block,
        flight_date=flight_date,
        created_by=request.user,
        updated_by=request.user
    )

    return success_response({
        'id': str(flight.id),
        'block_id': str(block.id),
        'flight_date': flight.flight_date.isoformat(),
        'created_at': flight.created_at.isoformat()
    }, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_flights(request):
    """
    List flights with filters.

    GET /api/flights/
    Query params:
    - block_id: Filter by block
    - start_date: Filter flights from date
    - end_date: Filter flights to date
    """
    queryset = Flight.objects.select_related('block', 'block__farm').all()

    block_id = request.query_params.get('block_id')
    if block_id:
        queryset = queryset.filter(block_id=block_id)

    start_date = request.query_params.get('start_date')
    if start_date:
        queryset = queryset.filter(flight_date__gte=start_date)

    end_date = request.query_params.get('end_date')
    if end_date:
        queryset = queryset.filter(flight_date__lte=end_date)

    flights = [
        {
            'id': str(f.id),
            'block_id': str(f.block.id),
            'block_name': f.block.name,
            'farm_name': f.block.farm.name,
            'flight_date': f.flight_date.isoformat(),
            'images_count': f.images.count(),
            'created_at': f.created_at.isoformat()
        }
        for f in queryset
    ]

    return success_response({'flights': flights, 'total': len(flights)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_flight(request, flight_id):
    """Get a flight with images."""
    try:
        flight = Flight.objects.prefetch_related('images').get(id=flight_id)
    except Flight.DoesNotExist:
        return failure_response('Flight not found', 404)

    return success_response({
        'id': str(flight.id),
        'block': {
            'id': str(flight.block.id),
            'name': flight.block.name
        },
        'flight_date': flight.flight_date.isoformat(),
        'images': [
            {
                'id': str(img.id),
                'file_path_id': img.file_path_id,
                'created_at': img.created_at.isoformat()
            }
            for img in flight.images.all()
        ],
        'created_at': flight.created_at.isoformat()
    })


# ==================== IMAGE ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_image(request):
    """
    Create an image record.

    POST /api/images/
    Request Body:
    {
        "flight_id": "uuid",
        "block_id": "uuid",
        "file_path_id": "s3://bucket/path/image.jpg"
    }
    """
    flight_id = request.data.get('flight_id')
    block_id = request.data.get('block_id')
    file_path_id = request.data.get('file_path_id')

    if not flight_id:
        return failure_response('flight_id is required')
    if not block_id:
        return failure_response('block_id is required')
    if not file_path_id:
        return failure_response('file_path_id is required')

    try:
        flight = Flight.objects.get(id=flight_id)
    except Flight.DoesNotExist:
        return failure_response('Flight not found', 404)

    try:
        block = Block.objects.get(id=block_id)
    except Block.DoesNotExist:
        return failure_response('Block not found', 404)

    image = Image.objects.create(
        flight=flight,
        block=block,
        file_path_id=file_path_id,
        created_by=request.user,
        updated_by=request.user
    )

    return success_response({
        'id': str(image.id),
        'flight_id': str(flight.id),
        'block_id': str(block.id),
        'file_path_id': image.file_path_id
    }, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_images(request):
    """List images with filters."""
    queryset = Image.objects.select_related('flight', 'block').all()

    flight_id = request.query_params.get('flight_id')
    if flight_id:
        queryset = queryset.filter(flight_id=flight_id)

    block_id = request.query_params.get('block_id')
    if block_id:
        queryset = queryset.filter(block_id=block_id)

    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 20))

    total = queryset.count()
    offset = (page - 1) * limit
    images = queryset[offset:offset + limit]

    data = [
        {
            'id': str(img.id),
            'flight_id': str(img.flight.id),
            'block_name': img.block.name,
            'file_path_id': img.file_path_id,
            'created_at': img.created_at.isoformat()
        }
        for img in images
    ]

    return success_response({
        'page': page,
        'limit': limit,
        'total': total,
        'total_pages': (total + limit - 1) // limit,
        'results': data
    })


# ==================== KPI ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_kpi(request):
    """
    Create a KPI record.

    POST /api/kpis/
    Request Body:
    {
        "block_id": "uuid",
        "period": "2024-Q1",
        "fungicide_reduction": 15.5,
        "fuel_reduction": 10.2,
        "co2_reduction": 50.0,
        "yield_reduction": -5.0
    }
    """
    block_id = request.data.get('block_id')
    period = request.data.get('period')

    if not block_id:
        return failure_response('block_id is required')
    if not period:
        return failure_response('period is required')

    try:
        block = Block.objects.get(id=block_id)
    except Block.DoesNotExist:
        return failure_response('Block not found', 404)

    # Check if KPI already exists for this period
    if KPI.objects.filter(block=block, period=period).exists():
        return failure_response(f'KPI already exists for period {period}')

    kpi = KPI.objects.create(
        block=block,
        period=period,
        fungicide_reduction=request.data.get('fungicide_reduction'),
        fuel_reduction=request.data.get('fuel_reduction'),
        co2_reduction=request.data.get('co2_reduction'),
        yield_reduction=request.data.get('yield_reduction'),
        created_by=request.user,
        updated_by=request.user
    )

    return success_response({
        'id': str(kpi.id),
        'block_id': str(block.id),
        'period': kpi.period
    }, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_kpis(request):
    """List KPIs with filters."""
    queryset = KPI.objects.select_related('block', 'block__farm').all()

    block_id = request.query_params.get('block_id')
    if block_id:
        queryset = queryset.filter(block_id=block_id)

    period = request.query_params.get('period')
    if period:
        queryset = queryset.filter(period=period)

    kpis = [
        {
            'id': str(k.id),
            'block_id': str(k.block.id),
            'block_name': k.block.name,
            'farm_name': k.block.farm.name,
            'period': k.period,
            'fungicide_reduction': float(k.fungicide_reduction) if k.fungicide_reduction else None,
            'fuel_reduction': float(k.fuel_reduction) if k.fuel_reduction else None,
            'co2_reduction': float(k.co2_reduction) if k.co2_reduction else None,
            'yield_reduction': float(k.yield_reduction) if k.yield_reduction else None,
        }
        for k in queryset
    ]

    return success_response({'kpis': kpis})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kpi(request, kpi_id):
    """Get a single KPI."""
    try:
        kpi = KPI.objects.select_related('block', 'block__farm').get(id=kpi_id)
    except KPI.DoesNotExist:
        return failure_response('KPI not found', 404)

    return success_response({
        'id': str(kpi.id),
        'block': {
            'id': str(kpi.block.id),
            'name': kpi.block.name,
            'farm_name': kpi.block.farm.name
        },
        'period': kpi.period,
        'fungicide_reduction': float(kpi.fungicide_reduction) if kpi.fungicide_reduction else None,
        'fuel_reduction': float(kpi.fuel_reduction) if kpi.fuel_reduction else None,
        'co2_reduction': float(kpi.co2_reduction) if kpi.co2_reduction else None,
        'yield_reduction': float(kpi.yield_reduction) if kpi.yield_reduction else None,
    })


# ==================== ACTION ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_action(request):
    """
    Create an action record.

    POST /api/actions/
    Request Body:
    {
        "block_id": "uuid",
        "period": "2024-01",
        "action_type": "SPRAY",
        "chemical_type": "FUNGICIDE",
        "quantity": 50.5,
        "cost": 500.00,
        "notes": "Applied fungicide treatment"
    }
    """
    block_id = request.data.get('block_id')
    period = request.data.get('period')
    action_type = request.data.get('action_type')

    if not block_id:
        return failure_response('block_id is required')
    if not period:
        return failure_response('period is required')
    if not action_type:
        return failure_response('action_type is required')

    if action_type not in ActionType.values:
        return failure_response(f'Invalid action_type. Valid values: {ActionType.values}')

    chemical_type = request.data.get('chemical_type', 'NONE')
    if chemical_type not in ChemicalType.values:
        return failure_response(f'Invalid chemical_type. Valid values: {ChemicalType.values}')

    try:
        block = Block.objects.get(id=block_id)
    except Block.DoesNotExist:
        return failure_response('Block not found', 404)

    action = Action.objects.create(
        block=block,
        period=period,
        action_type=action_type,
        chemical_type=chemical_type,
        quantity=request.data.get('quantity'),
        cost=request.data.get('cost'),
        yield_impact=request.data.get('yield_impact'),
        notes=request.data.get('notes', ''),
        created_by=request.user,
        updated_by=request.user
    )

    return success_response({
        'id': str(action.id),
        'block_id': str(block.id),
        'action_type': action.action_type,
        'period': action.period
    }, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_actions(request):
    """List actions with filters."""
    queryset = Action.objects.select_related('block', 'block__farm').all()

    block_id = request.query_params.get('block_id')
    if block_id:
        queryset = queryset.filter(block_id=block_id)

    action_type = request.query_params.get('action_type')
    if action_type:
        queryset = queryset.filter(action_type=action_type)

    period = request.query_params.get('period')
    if period:
        queryset = queryset.filter(period=period)

    actions = [
        {
            'id': str(a.id),
            'block_id': str(a.block.id),
            'block_name': a.block.name,
            'period': a.period,
            'action_type': a.action_type,
            'chemical_type': a.chemical_type,
            'quantity': float(a.quantity) if a.quantity else None,
            'cost': float(a.cost) if a.cost else None,
            'created_at': a.created_at.isoformat()
        }
        for a in queryset
    ]

    return success_response({'actions': actions})


# ==================== PHENOLOGY STAGE ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_phenology_stage(request):
    """
    Create a phenology stage record.

    POST /api/phenology-stages/
    Request Body:
    {
        "block_id": "uuid",
        "stage_name": "Bud Break",
        "start_date": "2024-03-15",
        "end_date": "2024-04-01",
        "notes": "Early bud break observed"
    }
    """
    block_id = request.data.get('block_id')
    stage_name = request.data.get('stage_name')
    start_date = request.data.get('start_date')

    if not block_id:
        return failure_response('block_id is required')
    if not stage_name:
        return failure_response('stage_name is required')
    if not start_date:
        return failure_response('start_date is required')

    start_date = _coerce_date(start_date)
    if not start_date:
        return failure_response('start_date must be a valid YYYY-MM-DD date')

    end_date = _coerce_date(request.data.get('end_date'))
    if request.data.get('end_date') and end_date is None:
        return failure_response('end_date must be a valid YYYY-MM-DD date')

    try:
        block = Block.objects.get(id=block_id)
    except Block.DoesNotExist:
        return failure_response('Block not found', 404)

    stage = PhenologyStage.objects.create(
        block=block,
        stage_name=stage_name,
        start_date=start_date,
        end_date=end_date,
        notes=request.data.get('notes', '')
    )

    return success_response({
        'id': str(stage.id),
        'block_id': str(block.id),
        'stage_name': stage.stage_name,
        'start_date': stage.start_date.isoformat()
    }, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_phenology_stages(request):
    """List phenology stages with filters."""
    queryset = PhenologyStage.objects.select_related('block', 'block__farm').all()

    block_id = request.query_params.get('block_id')
    if block_id:
        queryset = queryset.filter(block_id=block_id)

    stage_name = request.query_params.get('stage_name')
    if stage_name:
        queryset = queryset.filter(stage_name__icontains=stage_name)

    stages = [
        {
            'id': str(s.id),
            'block_id': str(s.block.id),
            'block_name': s.block.name,
            'farm_name': s.block.farm.name,
            'stage_name': s.stage_name,
            'start_date': s.start_date.isoformat(),
            'end_date': s.end_date.isoformat() if s.end_date else None,
            'notes': s.notes
        }
        for s in queryset
    ]

    return success_response({'phenology_stages': stages})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_phenology(request, block_id):
    """Get the current phenology stage for a block."""
    from django.utils import timezone
    today = timezone.now().date()

    try:
        current_stage = PhenologyStage.objects.filter(
            block_id=block_id,
            start_date__lte=today
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).order_by('-start_date').first()

        if not current_stage:
            # Try to get the most recent stage
            current_stage = PhenologyStage.objects.filter(
                block_id=block_id
            ).order_by('-start_date').first()
    except PhenologyStage.DoesNotExist:
        return failure_response('No phenology stage found', 404)

    if not current_stage:
        return failure_response('No phenology stages found for this block', 404)

    return success_response({
        'id': str(current_stage.id),
        'block_id': str(current_stage.block.id),
        'block_name': current_stage.block.name,
        'stage_name': current_stage.stage_name,
        'start_date': current_stage.start_date.isoformat(),
        'end_date': current_stage.end_date.isoformat() if current_stage.end_date else None,
        'notes': current_stage.notes
    })


# ==================== PREDICTION ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prediction(request):
    """
    Create a prediction record.

    POST /api/predictions/
    Request Body:
    {
        "block_id": "uuid",
        "phenology_stage_id": "uuid (optional)",
        "prediction_details": {"disease_risk": 0.3, "water_stress": 0.5},
        "result": "Low disease risk detected",
        "suggestion": "Continue current irrigation schedule",
        "stress_parameters": {"water": 0.5, "nutrient": 0.2, "disease": 0.3},
        "confidence_score": 85.5,
        "yield_prediction": 12.5
    }
    """
    block_id = request.data.get('block_id')

    if not block_id:
        return failure_response('block_id is required')

    try:
        block = Block.objects.get(id=block_id)
    except Block.DoesNotExist:
        return failure_response('Block not found', 404)

    phenology_stage_id = request.data.get('phenology_stage_id')
    phenology_stage = None
    if phenology_stage_id:
        try:
            phenology_stage = PhenologyStage.objects.get(id=phenology_stage_id)
        except PhenologyStage.DoesNotExist:
            return failure_response('Phenology stage not found', 404)

    prediction = Prediction.objects.create(
        block=block,
        phenology_stage=phenology_stage,
        prediction_details=request.data.get('prediction_details', {}),
        result=request.data.get('result', ''),
        suggestion=request.data.get('suggestion', ''),
        stress_parameters=request.data.get('stress_parameters', {}),
        confidence_score=request.data.get('confidence_score'),
        yield_prediction=request.data.get('yield_prediction'),
        created_by=request.user,
        updated_by=request.user
    )

    return success_response({
        'id': str(prediction.id),
        'block_id': str(block.id),
        'phenology_stage_id': str(phenology_stage.id) if phenology_stage else None,
        'confidence_score': float(prediction.confidence_score) if prediction.confidence_score else None
    }, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_predictions(request):
    """List predictions with filters."""
    queryset = Prediction.objects.select_related('block', 'block__farm', 'phenology_stage').all()

    block_id = request.query_params.get('block_id')
    if block_id:
        queryset = queryset.filter(block_id=block_id)

    phenology_stage_id = request.query_params.get('phenology_stage_id')
    if phenology_stage_id:
        queryset = queryset.filter(phenology_stage_id=phenology_stage_id)

    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 20))

    total = queryset.count()
    offset = (page - 1) * limit
    predictions = queryset[offset:offset + limit]

    data = [
        {
            'id': str(p.id),
            'block_id': str(p.block.id),
            'block_name': p.block.name,
            'farm_name': p.block.farm.name,
            'phenology_stage': p.phenology_stage.stage_name if p.phenology_stage else None,
            'result': p.result,
            'suggestion': p.suggestion,
            'confidence_score': float(p.confidence_score) if p.confidence_score else None,
            'yield_prediction': float(p.yield_prediction) if p.yield_prediction else None,
            'created_at': p.created_at.isoformat()
        }
        for p in predictions
    ]

    return success_response({
        'page': page,
        'limit': limit,
        'total': total,
        'total_pages': (total + limit - 1) // limit,
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prediction(request, prediction_id):
    """Get a single prediction with full details."""
    try:
        prediction = Prediction.objects.select_related('block', 'phenology_stage').get(id=prediction_id)
    except Prediction.DoesNotExist:
        return failure_response('Prediction not found', 404)

    return success_response({
        'id': str(prediction.id),
        'block': {
            'id': str(prediction.block.id),
            'name': prediction.block.name,
            'variety': prediction.block.variety
        },
        'phenology_stage': {
            'id': str(prediction.phenology_stage.id),
            'stage_name': prediction.phenology_stage.stage_name
        } if prediction.phenology_stage else None,
        'prediction_details': prediction.prediction_details,
        'result': prediction.result,
        'suggestion': prediction.suggestion,
        'stress_parameters': prediction.stress_parameters,
        'confidence_score': float(prediction.confidence_score) if prediction.confidence_score else None,
        'yield_prediction': float(prediction.yield_prediction) if prediction.yield_prediction else None,
        'created_at': prediction.created_at.isoformat(),
        'updated_at': prediction.updated_at.isoformat()
    })


# ==================== DASHBOARD/ANALYTICS ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_summary(request, farm_id):
    """Get a summary of all data for a farm."""
    try:
        farm = Farm.objects.prefetch_related('blocks').get(id=farm_id)
    except Farm.DoesNotExist:
        return failure_response('Farm not found', 404)

    blocks = farm.blocks.all()
    block_ids = [b.id for b in blocks]

    # Aggregate stats
    total_flights = Flight.objects.filter(block_id__in=block_ids).count()
    total_images = Image.objects.filter(block_id__in=block_ids).count()
    total_predictions = Prediction.objects.filter(block_id__in=block_ids).count()

    return success_response({
        'farm': {
            'id': str(farm.id),
            'name': farm.name,
            'organic_certified': farm.organic_certified
        },
        'blocks_count': len(blocks),
        'total_flights': total_flights,
        'total_images': total_images,
        'total_predictions': total_predictions,
        'blocks': [
            {
                'id': str(b.id),
                'name': b.name,
                'variety': b.variety
            }
            for b in blocks
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def block_analytics(request, block_id):
    """Get analytics data for a specific block."""
    try:
        block = Block.objects.select_related('farm').get(id=block_id)
    except Block.DoesNotExist:
        return failure_response('Block not found', 404)

    # Latest predictions
    latest_predictions = Prediction.objects.filter(block=block).order_by('-created_at')[:5]

    # Latest KPIs
    latest_kpis = KPI.objects.filter(block=block).order_by('-created_at')[:5]

    # Recent actions
    recent_actions = Action.objects.filter(block=block).order_by('-created_at')[:10]

    # Current phenology stage
    current_stage = PhenologyStage.objects.filter(block=block).order_by('-start_date').first()

    return success_response({
        'block': {
            'id': str(block.id),
            'name': block.name,
            'variety': block.variety,
            'farm_name': block.farm.name
        },
        'current_phenology_stage': {
            'stage_name': current_stage.stage_name,
            'start_date': current_stage.start_date.isoformat()
        } if current_stage else None,
        'latest_predictions': [
            {
                'id': str(p.id),
                'result': p.result,
                'confidence_score': float(p.confidence_score) if p.confidence_score else None,
                'created_at': p.created_at.isoformat()
            }
            for p in latest_predictions
        ],
        'latest_kpis': [
            {
                'id': str(k.id),
                'period': k.period,
                'fungicide_reduction': float(k.fungicide_reduction) if k.fungicide_reduction else None,
                'fuel_reduction': float(k.fuel_reduction) if k.fuel_reduction else None,
            }
            for k in latest_kpis
        ],
        'recent_actions': [
            {
                'id': str(a.id),
                'action_type': a.action_type,
                'chemical_type': a.chemical_type,
                'period': a.period
            }
            for a in recent_actions
        ]
    })