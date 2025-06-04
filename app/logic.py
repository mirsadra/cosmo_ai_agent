"""
Core Formulation Logic Engine
logic.py
Labrugis Ltd. 2025
"""

import uuid
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

from models import (
    FormulationRequest,
    FormulationResponse,
    FormulationIngredient,
    ComplianceCheck,
    ComplianceIssue,
    ComplianceStatus,
    OptimizationRequest,
    ProductType,
    IngredientFunction
)
from database import DatabaseManager


class FormulationEngine:
    """Advanced formulation engine with AI-driven optimization"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
        # Formulation rules and constraints
        self.product_type_rules = {
            ProductType.CREAM: {
                "water_range": (40, 80),
                "oil_range": (10, 30),
                "emulsifier_range": (2, 8),
                "preservative_range": (0.1, 1.0),
                "required_functions": [IngredientFunction.EMULSIFIER, IngredientFunction.PRESERVATIVE]
            },
            ProductType.SERUM: {
                "water_range": (70, 95),
                "oil_range": (0, 10),
                "active_range": (1, 20),
                "preservative_range": (0.1, 1.0),
                "required_functions": [IngredientFunction.PRESERVATIVE]
            },
            ProductType.LOTION: {
                "water_range": (60, 85),
                "oil_range": (5, 25),
                "emulsifier_range": (1, 5),
                "preservative_range": (0.1, 1.0),
                "required_functions": [IngredientFunction.EMULSIFIER, IngredientFunction.PRESERVATIVE]
            }
        }
        
        # Compatibility matrix for ingredient interactions
        self.compatibility_matrix = {
            "vitamin_c": {"incompatible": ["niacinamide"], "synergistic": ["vitamin_e"]},
            "retinol": {"incompatible": ["vitamin_c", "aha_bha"], "synergistic": ["hyaluronic_acid"]},
            "niacinamide": {"incompatible": ["vitamin_c"], "synergistic": ["hyaluronic_acid"]}
        }
    
    async def generate_formulation(self, request: FormulationRequest) -> FormulationResponse:
        """Generate optimized cosmetic formulation"""
        
        # Get base template for product type
        templates = await self.db.get_templates(request.product_type.value)
        base_template = templates[0] if templates else None
        
        # Initialize formulation
        formulation = []
        total_percentage = 0.0
        
        # Step 1: Add base ingredients from template
        if base_template:
            for base_ing in base_template.base_ingredients:
                ingredient = await self.db.get_ingredient_by_id(base_ing["ingredient_id"])
                if ingredient:
                    conc = base_ing["concentration"]
                    formulation.append(FormulationIngredient(
                        ingredient_id=ingredient.id,
                        name=ingredient.name,
                        inci_name=ingredient.inci_name,
                        concentration=conc,
                        function=ingredient.function
                    ))
                    total_percentage += conc
        
        # Step 2: Add required ingredients
        for req_ing_id in request.required_ingredients:
            if not any(f.ingredient_id == req_ing_id for f in formulation):
                ingredient = await self.db.get_ingredient_by_id(req_ing_id)
                if ingredient:
                    # Calculate optimal concentration
                    conc = await self._calculate_optimal_concentration(
                        ingredient, request, total_percentage
                    )
                    if conc > 0:
                        formulation.append(FormulationIngredient(
                            ingredient_id=ingredient.id,
                            name=ingredient.name,
                            inci_name=ingredient.inci_name,
                            concentration=conc,
                            function=ingredient.function
                        ))
                        total_percentage += conc
        
        # Step 3: Add complementary ingredients based on target properties
        if total_percentage < 99.0:
            complementary_ings = await self._select_complementary_ingredients(
                request, formulation, 99.0 - total_percentage
            )
            formulation.extend(complementary_ings)
            total_percentage = sum(f.concentration for f in formulation)
        
        # Step 4: Normalize to 100%
        if total_percentage != 100.0:
            formulation = self._normalize_formulation(formulation)
            total_percentage = 100.0
        
        # Step 5: Validate and optimize
        formulation = await self._validate_formulation(formulation, request)
        
        # Calculate properties
        cost = await self._calculate_cost(formulation)
        ph = await self._predict_ph(formulation)
        stability = await self._predict_stability(formulation)
        
        # Generate response
        response = FormulationResponse(
            id=str(uuid.uuid4()),
            product_type=request.product_type,
            ingredients=formulation,
            total_percentage=total_percentage,
            estimated_cost_per_kg=cost,
            predicted_ph=ph,
            stability_score=stability,
            compliance_status=ComplianceStatus.COMPLIANT,
            instructions=await self._generate_instructions(formulation, request.product_type),
            shelf_life_estimate=24
        )
        
        return response
    
    async def _calculate_optimal_concentration(
        self, 
        ingredient, 
        request: FormulationRequest, 
        current_total: float
    ) -> float:
        """Calculate optimal concentration for an ingredient"""
        
        # Get concentration limits
        min_conc = ingredient.min_concentration or 0.01
        max_conc = ingredient.max_concentration or 5.0
        
        # Adjust based on remaining percentage
        remaining = 100.0 - current_total
        max_conc = min(max_conc, remaining * 0.8)  # Don't use more than 80% of remaining
        
        # Function-based optimization
        if ingredient.function == IngredientFunction.ACTIVE:
            # Use higher concentration for actives if performance is priority
            if request.target_properties.get("performance_priority", False):
                return min(max_conc, max_conc * 0.8)
            else:
                return min(max_conc, max_conc * 0.5)
        
        elif ingredient.function == IngredientFunction.PRESERVATIVE:
            # Use minimum effective concentration
            return max(min_conc, min(max_conc, 0.5))
        
        elif ingredient.function == IngredientFunction.EMULSIFIER:
            # Product type dependent
            if request.product_type == ProductType.CREAM:
                return min(max_conc, 3.0)
            elif request.product_type == ProductType.LOTION:
                return min(max_conc, 2.0)
            else:
                return min(max_conc, 1.0)
        
        # Default calculation
        return min(max_conc, (min_conc + max_conc) / 2)
    
    async def _select_complementary_ingredients(
        self,
        request: FormulationRequest,
        current_formulation: List[FormulationIngredient],
        remaining_percentage: float
    ) -> List[FormulationIngredient]:
        """Select complementary ingredients based on target properties"""
        
        complementary = []
        used_functions = {f.function for f in current_formulation}
        
        # Get all available ingredients
        all_ingredients = await self.db.get_ingredients()
        
        # Filter out excluded ingredients
        available = [
            ing for ing in all_ingredients 
            if ing.id not in request.excluded_ingredients
            and ing.id not in [f.ingredient_id for f in current_formulation]
        ]
        
        # Priority scoring based on target properties
        scored_ingredients = []
        for ingredient in available:
            score = await self._score_ingredient_for_request(ingredient, request, used_functions)
            if score > 0:
                scored_ingredients.append((ingredient, score))
        
        # Sort by score
        scored_ingredients.sort(key=lambda x: x[1], reverse=True)
        
        # Select top ingredients within remaining percentage
        current_remaining = remaining_percentage
        for ingredient, score in scored_ingredients:
            if current_remaining <= 0.1:
                break
                
            conc = await self._calculate_optimal_concentration(
                ingredient, request, 100.0 - current_remaining
            )
            
            if conc > 0 and conc <= current_remaining:
                complementary.append(FormulationIngredient(
                    ingredient_id=ingredient.id,
                    name=ingredient.name,
                    inci_name=ingredient.inci_name,
                    concentration=conc,
                    function=ingredient.function
                ))
                current_remaining -= conc
                used_functions.add(ingredient.function)
        
        return complementary
    
    async def _score_ingredient_for_request(
        self,
        ingredient,
        request: FormulationRequest,
        used_functions: set
    ) -> float:
        """Score ingredient based on how well it fits the request"""
        score = 0.0
        
        # Function priority scoring
        function_priorities = {
            IngredientFunction.ACTIVE: 10.0,
            IngredientFunction.MOISTURIZER: 8.0,
            IngredientFunction.ANTIOXIDANT: 6.0,
            IngredientFunction.THICKENER: 4.0,
            IngredientFunction.FRAGRANCE: 2.0
        }
        
        base_score = function_priorities.get(ingredient.function, 1.0)
        
        # Boost score if function not yet used
        if ingredient.function not in used_functions:
            base_score *= 1.5
        
        # Natural preference bonus
        if request.natural_preference and ingredient.natural_origin:
            base_score *= 1.3
        
        # Cost consideration
        if request.max_cost_per_kg and ingredient.cost_per_kg:
            if ingredient.cost_per_kg > request.max_cost_per_kg * 0.1:  # High cost ingredient
                base_score *= 0.7
        
        # Target properties matching
        target_props = request.target_properties
        
        if "anti_aging" in target_props and ingredient.function == IngredientFunction.ACTIVE:
            if "peptide" in ingredient.name.lower() or "retinol" in ingredient.name.lower():
                base_score *= 1.5
        
        if "moisturizing" in target_props and ingredient.function == IngredientFunction.MOISTURIZER:
            base_score *= 1.4
        
        if "brightening" in target_props and "vitamin_c" in ingredient.id:
            base_score *= 1.4
        
        return base_score
    
    def _normalize_formulation(self, formulation: List[FormulationIngredient]) -> List[FormulationIngredient]:
        """Normalize formulation to sum to 100%"""
        total = sum(f.concentration for f in formulation)
        
        if total == 0:
            return formulation
        
        normalized = []
        for ingredient in formulation:
            new_conc = (ingredient.concentration / total) * 100.0
            normalized.append(FormulationIngredient(
                ingredient_id=ingredient.ingredient_id,
                name=ingredient.name,
                inci_name=ingredient.inci_name,
                concentration=round(new_conc, 2),
                function=ingredient.function
            ))
        
        return normalized
    
    async def _validate_formulation(
        self, 
        formulation: List[FormulationIngredient], 
        request: FormulationRequest
    ) -> List[FormulationIngredient]:
        """Validate and adjust formulation for safety and efficacy"""
        
        validated = []
        
        for ingredient in formulation:
            db_ingredient = await self.db.get_ingredient_by_id(ingredient.ingredient_id)
            if not db_ingredient:
                continue
            
            # Check concentration limits
            conc = ingredient.concentration
            if db_ingredient.max_concentration:
                conc = min(conc, db_ingredient.max_concentration)
            if db_ingredient.min_concentration:
                conc = max(conc, db_ingredient.min_concentration)
            
            # Check compatibility
            if await self._check_ingredient_compatibility(ingredient.ingredient_id, formulation):
                validated.append(FormulationIngredient(
                    ingredient_id=ingredient.ingredient_id,
                    name=ingredient.name,
                    inci_name=ingredient.inci_name,
                    concentration=conc,
                    function=ingredient.function
                ))
        
        return validated
    
    async def _check_ingredient_compatibility(
        self, 
        ingredient_id: str, 
        formulation: List[FormulationIngredient]
    ) -> bool:
        """Check if ingredient is compatible with other ingredients"""
        
        if ingredient_id not in self.compatibility_matrix:
            return True
        
        compatibility = self.compatibility_matrix[ingredient_id]
        formulation_ids = [f.ingredient_id for f in formulation]
        
        # Check for incompatible ingredients
        for incompatible in compatibility.get("incompatible", []):
            if incompatible in formulation_ids:
                return False
        
        return True
    
    async def _calculate_cost(self, formulation: List[FormulationIngredient]) -> Optional[float]:
        """Calculate estimated cost per kg"""
        total_cost = 0.0
        
        for ingredient in formulation:
            db_ingredient = await self.db.get_ingredient_by_id(ingredient.ingredient_id)
            if db_ingredient and db_ingredient.cost_per_kg:
                ingredient_cost = (ingredient.concentration / 100.0) * db_ingredient.cost_per_kg
                total_cost += ingredient_cost
        
        return round(total_cost, 2) if total_cost > 0 else None
    
    async def _predict_ph(self, formulation: List[FormulationIngredient]) -> Optional[float]:
        """Predict formulation pH"""
        # Simplified pH prediction based on ingredients
        ph_contributors = {
            "water": 7.0,
            "glycerin": 7.0,
            "vitamin_c": 3.5,
            "hyaluronic_acid": 6.5,
            "phenoxyethanol": 6.0
        }
        
        weighted_ph = 0.0
        total_weight = 0.0
        
        for ingredient in formulation:
            if ingredient.ingredient_id in ph_contributors:
                ph = ph_contributors[ingredient.ingredient_id]
                weight = ingredient.concentration
                weighted_ph += ph * weight
                total_weight += weight
        
        if total_weight > 0:
            return round(weighted_ph / total_weight, 1)
        
        return 6.5  # Default neutral pH
    
    async def _predict_stability(self, formulation: List[FormulationIngredient]) -> float:
        """Predict formulation stability score (0-10)"""
        stability_score = 7.0  # Base score
        
        # Check for stability-affecting ingredients
        has_emulsifier = any(f.function == IngredientFunction.EMULSIFIER for f in formulation)
        has_preservative = any(f.function == IngredientFunction.PRESERVATIVE for f in formulation)
        has_antioxidant = any(f.function == IngredientFunction.ANTIOXIDANT for f in formulation)
        
        if has_emulsifier:
            stability_score += 1.0
        if has_preservative:
            stability_score += 1.5
        if has_antioxidant:
            stability_score += 0.5
        
        # Check for unstable combinations
        ingredient_ids = [f.ingredient_id for f in formulation]
        if "vitamin_c" in ingredient_ids and "retinol" in ingredient_ids:
            stability_score -= 2.0
        
        return min(10.0, max(0.0, round(stability_score, 1)))
    
    async def _generate_instructions(
        self, 
        formulation: List[FormulationIngredient], 
        product_type: ProductType
    ) -> str:
        """Generate manufacturing instructions"""
        
        base_instructions = {
            ProductType.CREAM: (
                "1. Heat water phase ingredients to 70°C\n"
                "2. Heat oil phase ingredients to 70°C\n"
                "3. Slowly add oil phase to water phase with continuous mixing\n"
                "4. Cool to 40°C while mixing\n"
                "5. Add heat-sensitive actives below 40°C\n"
                "6. Adjust pH if needed\n"
                "7. Fill into sterilized containers"
            ),
            ProductType.SERUM: (
                "1. Mix water and glycols at room temperature\n"
                "2. Add water-soluble actives one by one\n"
                "3. Mix until completely dissolved\n"
                "4. Add preservative system\n"
                "5. Adjust pH to 5.5-6.5\n"
                "6. Fill into sterilized containers"
            ),
            ProductType.LOTION: (
                "1. Heat water phase to 65°C\n"
                "2. Heat oil phase to 65°C\n"
                "3. Add oil phase to water phase with mixing\n"
                "4. Cool to room temperature\n"
                "5. Add actives and preservatives\n"
                "6. Adjust pH and viscosity\n"
                "7. Fill into containers"
            )
        }
        
        return base_instructions.get(product_type, "Standard cosmetic manufacturing process")
    
    async def check_compliance(self, formulation_data: Dict[str, Any]) -> ComplianceCheck:
        """Check formulation compliance with UKES/EU regulations"""
        
        issues = []
        warnings = []
        prohibited = []
        concentration_violations = []
        
        regulatory_data = await self.db.get_regulatory_data()
        
        # Check each ingredient
        for ingredient_data in formulation_data.get("ingredients", []):
            ingredient_id = ingredient_data.get("ingredient_id")
            concentration = ingredient_data.get("concentration", 0)
            
            ingredient = await self.db.get_ingredient_by_id(ingredient_id)
            if not ingredient:
                continue
            
            # Check if prohibited
            if ingredient.prohibited_in_eu:
                prohibited.append(ingredient.name)
                issues.append(ComplianceIssue(
                    ingredient_id=ingredient_id,
                    ingredient_name=ingredient.name,
                    issue_type="prohibited",
                    severity="critical",
                    description=f"{ingredient.name} is prohibited in EU cosmetics",
                    recommendation="Remove this ingredient"
                ))
            
            # Check concentration limits
            if ingredient.max_concentration and concentration > ingredient.max_concentration:
                concentration_violations.append(
                    f"{ingredient.name}: {concentration}% (max: {ingredient.max_concentration}%)"
                )
                issues.append(ComplianceIssue(
                    ingredient_id=ingredient_id,
                    ingredient_name=ingredient.name,
                    issue_type="concentration_limit",
                    severity="high",
                    description=f"Concentration {concentration}% exceeds limit of {ingredient.max_concentration}%",
                    recommendation=f"Reduce concentration to max {ingredient.max_concentration}%"
                ))
            
            # Check restrictions
            if ingredient.restricted_in_eu:
                warnings.append(f"{ingredient.name} is restricted - verify compliance")
        
        # Determine overall status
        if issues:
            critical_issues = [i for i in issues if i.severity == "critical"]
            overall_status = ComplianceStatus.NON_COMPLIANT if critical_issues else ComplianceStatus.REQUIRES_REVIEW
        else:
            overall_status = ComplianceStatus.COMPLIANT
        
        return ComplianceCheck(
            overall_status=overall_status,
            ukes_compliant=(overall_status == ComplianceStatus.COMPLIANT),
            cpnp_ready=(overall_status == ComplianceStatus.COMPLIANT),
            issues=issues,
            warnings=warnings,
            prohibited_ingredients=prohibited,
            concentration_violations=concentration_violations,
            labeling_requirements=regulatory_data.get("labeling_requirements", [])
        )
    
    async def optimize_formulation(self, request: OptimizationRequest) -> FormulationResponse:
        """Optimize existing formulation based on target"""
        
        # This is a simplified optimization - in a full implementation,
        # you would use more sophisticated algorithms like genetic algorithms
        # or machine learning models
        
        # For now, return a basic optimization
        # In practice, implement specific optimization algorithms based on target
        
        return FormulationResponse(
            id=str(uuid.uuid4()),
            product_type=ProductType.CREAM,  # Default
            ingredients=[],
            total_percentage=100.0,
            compliance_status=ComplianceStatus.COMPLIANT,
            instructions="Optimization not yet implemented"
        )