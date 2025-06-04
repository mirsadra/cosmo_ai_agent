"""
Pydantic Models for Cosmetic Formulation AI Agent
models.py
Labrugis Ltd. 2025
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime


class ProductType(str, Enum):
    CREAM = "cream"
    LOTION = "lotion"
    SERUM = "serum"
    CLEANSER = "cleanser"
    TONER = "toner"
    MASK = "mask"
    SUNSCREEN = "sunscreen"
    SHAMPOO = "shampoo"
    CONDITIONER = "conditioner"


class IngredientFunction(str, Enum):
    EMULSIFIER = "emulsifier"
    MOISTURISER = "moisturiser"
    ACTIVE = "active"
    PRESERVATIVE = "preservative"
    THICKENER = "thickener"
    ANTIOXIDANT = "antioxidant"
    SURFACTANT = "surfactant"
    FRAGRANCE = "fragrance"
    COLORANT = "colorant"
    pH_ADJUSTER = "ph_adjuster"
    SOLVENT = "solvent"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"


class Ingredient(BaseModel):
    """Base ingredient model with UK/EU compliance data"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: str
    name: str
    inci_name: str
    cas_number: Optional[str] = None
    function: IngredientFunction
    category: str
    
    # Regulatory information
    max_concentration: Optional[float] = Field(None, ge=0, le=100)
    min_concentration: Optional[float] = Field(None, ge=0, le=100)
    prohibited_in_eu: bool = False
    restricted_in_eu: bool = False
    cpnp_reportable: bool = True
    
    # Physical/chemical properties
    molecular_weight: Optional[float] = None
    ph_range: Optional[Dict[str, float]] = None
    solubility: Optional[str] = None
    stability_notes: Optional[str] = None
    
    # Cost and sourcing
    cost_per_kg: Optional[float] = None
    supplier: Optional[str] = None
    natural_origin: bool = False
    organic_certified: bool = False
    
    @validator('max_concentration')
    def validate_max_concentration(cls, v, values):
        if v is not None and 'min_concentration' in values and values['min_concentration'] is not None:
            if v < values['min_concentration']:
                raise ValueError('max_concentration must be >= min_concentration')
        return v


class IngredientAdd(BaseModel):
    """Model for adding new ingredients"""
    name: str = Field(..., min_length=1)
    inci_name: str = Field(..., min_length=1)
    cas_number: Optional[str] = None
    function: IngredientFunction
    category: str = Field(..., min_length=1)
    max_concentration: Optional[float] = Field(None, ge=0, le=100)
    min_concentration: Optional[float] = Field(None, ge=0, le=100)
    prohibited_in_eu: bool = False
    restricted_in_eu: bool = False
    cost_per_kg: Optional[float] = Field(None, gt=0)
    natural_origin: bool = False


class FormulationIngredient(BaseModel):
    """Ingredient with specific concentration in formulation"""
    ingredient_id: str
    name: str
    inci_name: str
    concentration: float = Field(..., ge=0, le=100)
    function: IngredientFunction
    
    
class FormulationRequest(BaseModel):
    """Request for generating a new formulation"""
    product_type: ProductType
    target_properties: Dict[str, Any] = Field(default_factory=dict)
    required_ingredients: List[str] = Field(default_factory=list)
    excluded_ingredients: List[str] = Field(default_factory=list)
    max_cost_per_kg: Optional[float] = Field(None, gt=0)
    natural_preference: bool = False
    target_ph: Optional[float] = Field(None, ge=0, le=14)
    stability_priority: bool = True
    
    # UK specific requirements
    ukes_compliant: bool = True
    cpnp_ready: bool = True


class FormulationResponse(BaseModel):
    """Response containing generated formulation"""
    id: str
    product_type: ProductType
    ingredients: List[FormulationIngredient]
    total_percentage: float
    estimated_cost_per_kg: Optional[float] = None
    predicted_ph: Optional[float] = None
    stability_score: Optional[float] = Field(None, ge=0, le=10)
    compliance_status: ComplianceStatus
    
    # Additional information
    instructions: Optional[str] = None
    shelf_life_estimate: Optional[int] = None  # months
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('total_percentage')
    def validate_total_percentage(cls, v):
        if not (99.0 <= v <= 100.0):
            raise ValueError('Total percentage should be between 99-100%')
        return v


class ComplianceIssue(BaseModel):
    """Individual compliance issue"""
    ingredient_id: str
    ingredient_name: str
    issue_type: str
    severity: str  # low, medium, high, critical
    description: str
    recommendation: Optional[str] = None


class ComplianceCheck(BaseModel):
    """Compliance check results"""
    overall_status: ComplianceStatus
    ukes_compliant: bool
    cpnp_ready: bool
    issues: List[ComplianceIssue] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Regulatory summary
    prohibited_ingredients: List[str] = Field(default_factory=list)
    concentration_violations: List[str] = Field(default_factory=list)
    labeling_requirements: List[str] = Field(default_factory=list)


class OptimizationTarget(str, Enum):
    COST = "cost"
    STABILITY = "stability"
    PERFORMANCE = "performance"
    NATURALNESS = "naturalness"


class OptimizationRequest(BaseModel):
    """Request for optimizing existing formulation"""
    formulation_id: Optional[str] = None
    current_formulation: Optional[List[FormulationIngredient]] = None
    optimization_target: OptimizationTarget
    constraints: Dict[str, Any] = Field(default_factory=dict)
    max_changes: int = Field(3, ge=1, le=10)


class PeptideData(BaseModel):
    """Specialized model for peptide ingredients"""
    id: str
    name: str
    sequence: str
    molecular_weight: float
    function: str
    stability_ph_range: Dict[str, float]
    max_concentration: float
    cost_per_gram: float
    efficacy_studies: List[str] = Field(default_factory=list)
    
    # Regulatory specific
    novel_ingredient: bool = False
    safety_assessment_required: bool = True


class FormularyTemplate(BaseModel):
    """Template for specific product types"""
    id: str
    name: str
    product_type: ProductType
    base_ingredients: List[Dict[str, Union[str, float]]]
    variable_ingredients: List[str]
    instructions: str
    typical_cost_range: Dict[str, float]
    stability_notes: Optional[str] = None