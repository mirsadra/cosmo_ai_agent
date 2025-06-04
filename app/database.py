"""
Database Manager for Cosmetic Formulation AI Agent
Handles ingredient database, templates, and regulatory data
database.py
Labrugis Ltd. 2025
"""

import json
import aiofiles
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
import uuid
from datetime import datetime

from models import (
    Ingredient, 
    IngredientAdd, 
    FormularyTemplate, 
    PeptideData,
    IngredientFunction,
    ProductType
)


class DatabaseManager:
    """Manages ingredient database and formulation templates"""
    
    def __init__(self, data_path: str = "."):
        self.data_path = Path(data_path)
        self.ingredients_file = self.data_path / "ingredients.json"
        self.peptides_file = self.data_path / "peptides.json"
        self.formulary_file = self.data_path / "formulary.json"
        self.regulatory_file = self.data_path / "regulatory_data.json"
        
        # In-memory storage for fast access
        self.ingredients: Dict[str, Ingredient] = {}
        self.peptides: Dict[str, PeptideData] = {}
        self.templates: Dict[str, FormularyTemplate] = {}
        self.regulatory_data: Dict[str, Any] = {}
    
    async def initialize(self):
        """Initialize database with default data"""
        await self._load_all_data()
        
        # Create default data if files don't exist
        if not self.ingredients:
            await self._create_default_ingredients()
        
        if not self.peptides:
            await self._create_default_peptides()
            
        if not self.templates:
            await self._create_default_templates()
            
        if not self.regulatory_data:
            await self._create_regulatory_data()
    
    async def _load_all_data(self):
        """Load all data from JSON files"""
        tasks = [
            self._load_ingredients(),
            self._load_peptides(),
            self._load_templates(),
            self._load_regulatory_data()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _load_ingredients(self):
        """Load ingredients from JSON file"""
        try:
            if self.ingredients_file.exists():
                async with aiofiles.open(self.ingredients_file, 'r') as f:
                    data = json.loads(await f.read())
                    self.ingredients = {
                        k: Ingredient(**v) for k, v in data.items()
                    }
        except Exception as e:
            print(f"Error loading ingredients: {e}")
            self.ingredients = {}
    
    async def _load_peptides(self):
        """Load peptides from JSON file"""
        try:
            if self.peptides_file.exists():
                async with aiofiles.open(self.peptides_file, 'r') as f:
                    data = json.loads(await f.read())
                    self.peptides = {
                        k: PeptideData(**v) for k, v in data.items()
                    }
        except Exception as e:
            print(f"Error loading peptides: {e}")
            self.peptides = {}
    
    async def _load_templates(self):
        """Load formulation templates"""
        try:
            if self.formulary_file.exists():
                async with aiofiles.open(self.formulary_file, 'r') as f:
                    data = json.loads(await f.read())
                    self.templates = {
                        k: FormularyTemplate(**v) for k, v in data.items()
                    }
        except Exception as e:
            print(f"Error loading templates: {e}")
            self.templates = {}
    
    async def _load_regulatory_data(self):
        """Load regulatory compliance data"""
        try:
            if self.regulatory_file.exists():
                async with aiofiles.open(self.regulatory_file, 'r') as f:
                    self.regulatory_data = json.loads(await f.read())
        except Exception as e:
            print(f"Error loading regulatory data: {e}")
            self.regulatory_data = {}
    
    async def _create_default_ingredients(self):
        """Create default ingredient database"""
        default_ingredients = {
            "water": Ingredient(
                id="water",
                name="Purified Water",
                inci_name="Aqua",
                function=IngredientFunction.SOLVENT,
                category="base",
                max_concentration=95.0,
                min_concentration=10.0,
                cost_per_kg=0.50,
                natural_origin=True
            ),
            "glycerin": Ingredient(
                id="glycerin",
                name="Glycerin",
                inci_name="Glycerin",
                function=IngredientFunction.MOISTURISER,
                category="humectant",
                max_concentration=10.0,
                min_concentration=0.5,
                cost_per_kg=2.50,
                natural_origin=True
            ),
            "cetyl_alcohol": Ingredient(
                id="cetyl_alcohol",
                name="Cetyl Alcohol",
                inci_name="Cetyl Alcohol",
                function=IngredientFunction.EMULSIFIER,
                category="emulsifier",
                max_concentration=5.0,
                min_concentration=0.5,
                cost_per_kg=4.20,
                natural_origin=True
            ),
            "phenoxyethanol": Ingredient(
                id="phenoxyethanol",
                name="Phenoxyethanol",
                inci_name="Phenoxyethanol",
                function=IngredientFunction.PRESERVATIVE,
                category="preservative",
                max_concentration=1.0,
                min_concentration=0.1,
                cost_per_kg=12.50,
                restricted_in_eu=True
            ),
            "hyaluronic_acid": Ingredient(
                id="hyaluronic_acid",
                name="Hyaluronic Acid",
                inci_name="Sodium Hyaluronate",
                function=IngredientFunction.ACTIVE,
                category="active",
                max_concentration=2.0,
                min_concentration=0.01,
                cost_per_kg=350.00,
                natural_origin=True
            ),
            "vitamin_c": Ingredient(
                id="vitamin_c",
                name="Vitamin C",
                inci_name="Ascorbic Acid",
                function=IngredientFunction.ANTIOXIDANT,
                category="active",
                max_concentration=20.0,
                min_concentration=0.1,
                cost_per_kg=45.00,
                stability_notes="Light and air sensitive"
            )
        }
        
        self.ingredients = default_ingredients
        await self._save_ingredients()
    
    async def _create_default_peptides(self):
        """Create default peptide database"""
        default_peptides = {
            "matrixyl_3000": PeptideData(
                id="matrixyl_3000",
                name="Matrixyl 3000",
                sequence="Pal-GHK + Pal-GQPR",
                molecular_weight=578.73,
                function="anti-aging",
                stability_ph_range={"min": 5.0, "max": 7.0},
                max_concentration=8.0,
                cost_per_gram=125.00,
                efficacy_studies=[
                    "Reduces wrinkles by 45% in 8 weeks",
                    "Increases collagen synthesis by 117%"
                ],
                safety_assessment_required=True
            ),
            "argireline": PeptideData(
                id="argireline",
                name="Argireline",
                sequence="Ac-EEMQRR-NH2",
                molecular_weight=888.99,
                function="expression_lines",
                stability_ph_range={"min": 4.0, "max": 8.0},
                max_concentration=10.0,
                cost_per_gram=280.00,
                efficacy_studies=[
                    "Reduces expression lines by 17% in 15 days"
                ],
                safety_assessment_required=True
            )
        }
        
        self.peptides = default_peptides
        await self._save_peptides()
    
    async def _create_default_templates(self):
        """Create default formulation templates"""
        default_templates = {
            "basic_cream": FormularyTemplate(
                id="basic_cream",
                name="Basic Moisturizing Cream",
                product_type=ProductType.CREAM,
                base_ingredients=[
                    {"ingredient_id": "water", "concentration": 65.0},
                    {"ingredient_id": "glycerin", "concentration": 5.0},
                    {"ingredient_id": "cetyl_alcohol", "concentration": 3.0},
                    {"ingredient_id": "phenoxyethanol", "concentration": 0.5}
                ],
                variable_ingredients=["hyaluronic_acid", "vitamin_c"],
                instructions="Heat oil and water phases separately to 70°C. Add oil phase to water phase with mixing.",
                typical_cost_range={"min": 8.50, "max": 25.00}
            ),
            "anti_aging_serum": FormularyTemplate(
                id="anti_aging_serum",
                name="Anti-Aging Serum",
                product_type=ProductType.SERUM,
                base_ingredients=[
                    {"ingredient_id": "water", "concentration": 80.0},
                    {"ingredient_id": "glycerin", "concentration": 10.0},
                    {"ingredient_id": "phenoxyethanol", "concentration": 0.3}
                ],
                variable_ingredients=["hyaluronic_acid", "matrixyl_3000", "argireline"],
                instructions="Mix all ingredients at room temperature. Adjust pH to 6.0-6.5.",
                typical_cost_range={"min": 35.00, "max": 120.00}
            )
        }
        
        self.templates = default_templates
        await self._save_templates()
    
    async def _create_regulatory_data(self):
        """Create regulatory compliance database"""
        self.regulatory_data = {
            "prohibited_substances": [
                "hydroquinone",
                "mercury_compounds",
                "lead_compounds"
            ],
            "restricted_concentrations": {
                "phenoxyethanol": 1.0,
                "benzyl_alcohol": 1.0,
                "salicylic_acid": 2.0
            },
            "cpnp_requirements": {
                "safety_assessment": True,
                "product_information_file": True,
                "responsible_person": True
            },
            "labeling_requirements": [
                "INCI names in descending order",
                "Warnings and precautions",
                "Batch number and expiry date",
                "Net content",
                "Function of product"
            ]
        }
        await self._save_regulatory_data()
    
    async def get_ingredients(
        self, 
        category: Optional[str] = None,
        function: Optional[str] = None,
        limit: int = 100
    ) -> List[Ingredient]:
        """Get ingredients with optional filtering"""
        ingredients = list(self.ingredients.values())
        
        if category:
            ingredients = [i for i in ingredients if i.category == category]
        
        if function:
            ingredients = [i for i in ingredients if i.function == function]
        
        return ingredients[:limit]
    
    async def get_ingredient_by_id(self, ingredient_id: str) -> Optional[Ingredient]:
        """Get specific ingredient by ID"""
        return self.ingredients.get(ingredient_id)
    
    async def add_ingredient(self, ingredient_data: IngredientAdd) -> str:
        """Add new ingredient to database"""
        ingredient_id = str(uuid.uuid4())
        
        # Check if ingredient already exists
        existing = [i for i in self.ingredients.values() 
                   if i.inci_name.lower() == ingredient_data.inci_name.lower()]
        if existing:
            raise ValueError(f"Ingredient {ingredient_data.inci_name} already exists")
        
        ingredient = Ingredient(
            id=ingredient_id,
            **ingredient_data.model_dump()
        )
        
        self.ingredients[ingredient_id] = ingredient
        await self._save_ingredients()
        return ingredient_id
    
    async def get_templates(self, product_type: Optional[str] = None) -> List[FormularyTemplate]:
        """Get formulation templates"""
        templates = list(self.templates.values())
        
        if product_type:
            templates = [t for t in templates if t.product_type == product_type]
        
        return templates
    
    async def get_peptides(self) -> List[PeptideData]:
        """Get all peptides"""
        return list(self.peptides.values())
    
    async def get_regulatory_data(self) -> Dict[str, Any]:
        """Get regulatory compliance data"""
        return self.regulatory_data
    
    # Save methods
    async def _save_ingredients(self):
        """Save ingredients to JSON file"""
        data = {k: v.model_dump() for k, v in self.ingredients.items()}
        async with aiofiles.open(self.ingredients_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    async def _save_peptides(self):
        """Save peptides to JSON file"""
        data = {k: v.model_dump() for k, v in self.peptides.items()}
        async with aiofiles.open(self.peptides_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    async def _save_templates(self):
        """Save templates to JSON file"""
        data = {k: v.model_dump() for k, v in self.templates.items()}
        async with aiofiles.open(self.formulary_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    async def _save_regulatory_data(self):
        """Save regulatory data to JSON file"""
        async with aiofiles.open(self.regulatory_file, 'w') as f:
            await f.write(json.dumps(self.regulatory_data, indent=2, default=str))

