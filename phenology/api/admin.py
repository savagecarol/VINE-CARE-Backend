from django.contrib import admin
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin

from .models import (
    Farm, Location, Block, Flight, Image, KPI,
    Action, Prediction, PhenologyStage
)


admin.site.register(Token, TokenAdmin)


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    """Admin interface for Farm model."""
    list_display = ('id', 'name', 'organic_certified', 'created_at', 'created_by')
    list_filter = ('organic_certified', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'organic_certified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin interface for Location model."""
    list_display = ('id', 'latitude', 'longitude', 'farm', 'block', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('farm__name', 'block__name')
    readonly_fields = ('id', 'created_at')

    fieldsets = (
        ('Location Details', {
            'fields': ('id', 'latitude', 'longitude')
        }),
        ('Association', {
            'fields': ('farm', 'block')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """Admin interface for Block model."""
    list_display = ('id', 'name', 'variety', 'farm', 'created_at')
    list_filter = ('variety', 'created_at')
    search_fields = ('name', 'farm__name', 'variety')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'farm', 'name', 'variety', 'other_language_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    """Admin interface for Flight model."""
    list_display = ('id', 'block', 'flight_date', 'created_at', 'created_by')
    list_filter = ('flight_date', 'created_at')
    search_fields = ('block__name', 'block__farm__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'flight_date'
    ordering = ('-flight_date',)

    fieldsets = (
        ('Flight Information', {
            'fields': ('id', 'block', 'flight_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """Admin interface for Image model."""
    list_display = ('id', 'flight', 'block', 'file_path_id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('block__name', 'file_path_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Image Information', {
            'fields': ('id', 'flight', 'block', 'file_path_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    """Admin interface for KPI model."""
    list_display = ('id', 'block', 'period', 'fungicide_reduction', 'fuel_reduction', 'co2_reduction', 'created_at')
    list_filter = ('period', 'created_at')
    search_fields = ('block__name', 'period')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('KPI Information', {
            'fields': ('id', 'block', 'period')
        }),
        ('Metrics', {
            'fields': ('fungicide_reduction', 'fuel_reduction', 'co2_reduction', 'yield_reduction')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    """Admin interface for Action model."""
    list_display = ('id', 'block', 'period', 'action_type', 'chemical_type', 'quantity', 'cost', 'created_at')
    list_filter = ('action_type', 'chemical_type', 'created_at')
    search_fields = ('block__name', 'period', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Action Information', {
            'fields': ('id', 'block', 'period', 'action_type', 'chemical_type')
        }),
        ('Details', {
            'fields': ('quantity', 'cost', 'yield_impact', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PhenologyStage)
class PhenologyStageAdmin(admin.ModelAdmin):
    """Admin interface for PhenologyStage model."""
    list_display = ('id', 'block', 'stage_name', 'start_date', 'end_date', 'created_at')
    list_filter = ('stage_name', 'start_date', 'created_at')
    search_fields = ('block__name', 'stage_name', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

    fieldsets = (
        ('Stage Information', {
            'fields': ('id', 'block', 'stage_name', 'start_date', 'end_date', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    """Admin interface for Prediction model."""
    list_display = ('id', 'block', 'phenology_stage', 'confidence_score', 'yield_prediction', 'created_at')
    list_filter = ('created_at', 'confidence_score')
    search_fields = ('block__name', 'result', 'suggestion')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Prediction Information', {
            'fields': ('id', 'block', 'phenology_stage')
        }),
        ('Prediction Data', {
            'fields': ('prediction_details', 'result', 'suggestion', 'stress_parameters')
        }),
        ('Metrics', {
            'fields': ('confidence_score', 'yield_prediction')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make JSON fields display better."""
        readonly = list(self.readonly_fields)
        return readonly