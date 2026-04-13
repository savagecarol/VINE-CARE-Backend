import uuid
from django.db import models
from django.conf import settings


class Farm(models.Model):
    """
    Farm entity representing a vineyard/farm in the agriculture platform.
    One Farm has many Blocks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text='Name of the farm')
    organic_certified = models.BooleanField(default=False, help_text='Whether farm is organically certified')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='farms_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='farms_updated'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['organic_certified']),
        ]

    def __str__(self):
        return self.name


class Location(models.Model):
    """
    Location entity for geographic coordinates.
    Supports both Farm and Block locations through generic foreign key pattern.
    A Farm or Block can have multiple Locations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Generic relationship to support both Farm and Block
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='locations'
    )
    block = models.ForeignKey(
        'Block',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='locations'
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=8, help_text='Latitude coordinate')
    longitude = models.DecimalField(max_digits=11, decimal_places=8, help_text='Longitude coordinate')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farm']),
            models.Index(fields=['block']),
        ]

    def __str__(self):
        return f"({self.latitude}, {self.longitude})"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Ensure location is associated with either farm or block, not both
        if self.farm and self.block:
            raise ValidationError('Location must be associated with either farm or block, not both.')
        if not self.farm and not self.block:
            raise ValidationError('Location must be associated with a farm or block.')


class Block(models.Model):
    """
    Block entity representing a section within a farm/vineyard.
    One Farm has many Blocks.
    One Block has many Flights, KPIs, Actions, Predictions, PhenologyStates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name='blocks'
    )
    variety = models.CharField(max_length=255, help_text='Grape variety planted in this block')
    name = models.CharField(max_length=255, help_text='Block name/identifier')
    other_language_name = models.CharField(max_length=255, blank=True, null=True, help_text='Alternative name in local language')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farm']),
            models.Index(fields=['variety']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.variety}) - {self.farm.name}"


class Flight(models.Model):
    """
    Flight entity representing a drone/satellite flight over a block.
    One Block has many Flights.
    One Flight has many Images.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name='flights'
    )
    flight_date = models.DateField(help_text='Date of the flight')
    altitude_meters = models.IntegerField(null=True, blank=True, help_text='Drone flight altitude in meters (e.g. 100, 120, 140)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='flights_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='flights_updated'
    )

    class Meta:
        ordering = ['-flight_date']
        indexes = [
            models.Index(fields=['block', 'flight_date']),
            models.Index(fields=['flight_date']),
        ]

    def __str__(self):
        return f"Flight {self.id} - {self.block.name} on {self.flight_date}"


class Image(models.Model):
    """
    Image entity representing captured images during a flight.
    One Flight has many Images.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name='images'
    )
    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name='images'
    )
    file_path_id = models.CharField(max_length=500, help_text='S3 path or file identifier')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='images_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='images_updated'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['flight']),
            models.Index(fields=['block']),
        ]

    def __str__(self):
        return f"Image {self.id} - Flight {self.flight.id}"


class KPI(models.Model):
    """
    KPI (Key Performance Indicator) entity tracking block metrics.
    One Block has many KPIs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name='kpis'
    )
    period = models.CharField(max_length=50, help_text='Time period (e.g., "2024-Q1", "2024-01")')
    fungicide_reduction = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Fungicide reduction percentage'
    )
    fuel_reduction = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Fuel reduction percentage'
    )
    co2_reduction = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='CO2 reduction in kg'
    )
    yield_reduction = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Yield reduction percentage (negative = increase)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kpis_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kpis_updated'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['block', 'period']),
            models.Index(fields=['period']),
        ]
        unique_together = ['block', 'period']

    def __str__(self):
        return f"KPI {self.period} - {self.block.name}"


class ActionType(models.TextChoices):
    """Types of agricultural actions."""
    SPRAY = 'SPRAY', 'Spray Application'
    IRRIGATE = 'IRRIGATE', 'Irrigation'
    HARVEST = 'HARVEST', 'Harvest'
    PRUNE = 'PRUNE', 'Pruning'
    FERTILIZE = 'FERTILIZE', 'Fertilization'
    SCOUT = 'SCOUT', 'Scouting'
    OTHER = 'OTHER', 'Other'


class ChemicalType(models.TextChoices):
    """Types of chemicals used in actions."""
    FUNGICIDE = 'FUNGICIDE', 'Fungicide'
    INSECTICIDE = 'INSECTICIDE', 'Insecticide'
    HERBICIDE = 'HERBICIDE', 'Herbicide'
    FERTILIZER = 'FERTILIZER', 'Fertilizer'
    OTHER = 'OTHER', 'Other'
    NONE = 'NONE', 'None'


class Action(models.Model):
    """
    Action entity representing agricultural actions taken on a block.
    One Block has many Actions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    period = models.CharField(max_length=50, help_text='Time period (e.g., "2024-Q1", "2024-01")')
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        help_text='Type of action performed'
    )
    chemical_type = models.CharField(
        max_length=20,
        choices=ChemicalType.choices,
        default=ChemicalType.NONE,
        help_text='Type of chemical used'
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Quantity applied (liters/kg)'
    )
    cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Cost of action in local currency'
    )
    yield_impact = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Impact on yield (percentage)'
    )
    notes = models.TextField(blank=True, null=True, help_text='Additional notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions_updated'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['block', 'period']),
            models.Index(fields=['action_type']),
            models.Index(fields=['period']),
        ]

    def __str__(self):
        return f"{self.action_type} - {self.block.name} ({self.period})"


class PhenologyStage(models.Model):
    """
    PhenologyStage entity representing growth stages for vines.
    One Block has many PhenologyStates (historical tracking).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name='phenology_stages'
    )
    stage_name = models.CharField(max_length=100, help_text='Growth stage name (e.g., Bud Break, Flowering, Veraison)')
    start_date = models.DateField(help_text='Start date of this stage')
    end_date = models.DateField(null=True, blank=True, help_text='End date of this stage')
    notes = models.TextField(blank=True, null=True, help_text='Additional notes about this stage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['block', 'start_date']),
            models.Index(fields=['stage_name']),
        ]

    def __str__(self):
        return f"{self.stage_name} - {self.block.name} ({self.start_date})"


class Prediction(models.Model):
    """
    Prediction entity containing AI/ML predictions for a block.
    One Block has many Predictions.
    Links to PhenologyStage for stage-specific predictions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    phenology_stage = models.ForeignKey(
        PhenologyStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='predictions'
    )
    prediction_details = models.JSONField(
        default=dict,
        help_text='Detailed prediction data as JSON'
    )
    result = models.CharField(max_length=255, blank=True, null=True, help_text='Prediction result summary')
    suggestion = models.TextField(blank=True, null=True, help_text='AI-generated suggestions')
    stress_parameters = models.JSONField(
        default=dict,
        help_text='Stress level parameters (water, nutrient, disease, etc.)'
    )
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Model confidence score (0-100)'
    )
    yield_prediction = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Predicted yield (tons/hectare)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='predictions_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='predictions_updated'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['block']),
            models.Index(fields=['phenology_stage']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Prediction for {self.block.name} - {self.created_at.date()}"