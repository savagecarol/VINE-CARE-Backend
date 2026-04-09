from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # Auth
    path('auth/register/', views.register_view, name='auth_register'),
    path('auth/login/', views.login_view, name='auth_login'),

    # Farm endpoints
    path('farms/', views.list_farms, name='list_farms'),
    path('farms/create/', views.create_farm, name='create_farm'),
    path('farms/<uuid:farm_id>/', views.get_farm, name='get_farm'),
    path('farms/<uuid:farm_id>/update/', views.update_farm, name='update_farm'),
    path('farms/<uuid:farm_id>/delete/', views.delete_farm, name='delete_farm'),
    path('farms/<uuid:farm_id>/summary/', views.farm_summary, name='farm_summary'),

    # Block endpoints
    path('blocks/', views.list_blocks, name='list_blocks'),
    path('blocks/create/', views.create_block, name='create_block'),
    path('blocks/<uuid:block_id>/', views.get_block, name='get_block'),
    path('blocks/<uuid:block_id>/analytics/', views.block_analytics, name='block_analytics'),

    # Flight endpoints
    path('flights/', views.list_flights, name='list_flights'),
    path('flights/create/', views.create_flight, name='create_flight'),
    path('flights/<uuid:flight_id>/', views.get_flight, name='get_flight'),

    # Image endpoints
    path('images/', views.list_images, name='list_images'),
    path('images/create/', views.create_image, name='create_image'),

    # KPI endpoints
    path('kpis/', views.list_kpis, name='list_kpis'),
    path('kpis/create/', views.create_kpi, name='create_kpi'),
    path('kpis/<uuid:kpi_id>/', views.get_kpi, name='get_kpi'),

    # Action endpoints
    path('actions/', views.list_actions, name='list_actions'),
    path('actions/create/', views.create_action, name='create_action'),

    # Phenology Stage endpoints
    path('phenology-stages/', views.list_phenology_stages, name='list_phenology_stages'),
    path('phenology-stages/create/', views.create_phenology_stage, name='create_phenology_stage'),
    path('phenology-stages/current/<uuid:block_id>/', views.get_current_phenology, name='get_current_phenology'),

    # Prediction endpoints
    path('predictions/', views.list_predictions, name='list_predictions'),
    path('predictions/create/', views.create_prediction, name='create_prediction'),
    path('predictions/<uuid:prediction_id>/', views.get_prediction, name='get_prediction'),
]