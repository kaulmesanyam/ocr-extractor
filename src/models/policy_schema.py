"""Pydantic models for car insurance policy extraction schema

NOTE: Currently not actively used in the extraction pipeline.
The system uses JSON schema validation (validator.json) instead.
These models are kept for:
- Future use if Pydantic validation is needed
- Type hints and IDE support
- Reference documentation

If you need to switch to Pydantic validation, update schema_validator.py
to use these models instead of JSON schema validation.
"""

from typing import Optional, List, Union
from pydantic import BaseModel, Field


class Policyholder(BaseModel):
    """Policyholder information"""
    name: str = Field(..., description="Full name of the insured/policyholder")
    address: str = Field(..., description="Postal or residential address")
    occupation: str = Field(..., description="Profession or business type")
    namedDrivers: Optional[List[str]] = Field(default=None, description="List of specified drivers")


class LiabilityLimits(BaseModel):
    """Liability limits for third-party claims"""
    bodilyInjury: float = Field(..., description="Maximum payout for bodily injury claims")
    propertyDamage: float = Field(..., description="Maximum payout for property damage claims")


class Excess(BaseModel):
    """Deductible amounts"""
    thirdPartyProperty: Optional[float] = Field(default=None, description="Third party property excess")
    youngDriver: Optional[float] = Field(default=None, description="Young driver excess")
    inexperiencedDriver: Optional[float] = Field(default=None, description="Inexperienced driver excess")
    unnamedDriver: Optional[float] = Field(default=None, description="Unnamed driver excess")


class LimitationsOnUse(BaseModel):
    """Usage restrictions"""
    details: List[str] = Field(..., description="List of usage restriction clauses")


class Coverage(BaseModel):
    """Coverage details"""
    typeOfCover: str = Field(..., description="Level of insurance (e.g., third party only, comprehensive)")
    liabilityLimits: LiabilityLimits = Field(..., description="Maximum payout for third-party claims")
    excess: Excess = Field(..., description="Deductible amounts")
    limitationsOnUse: LimitationsOnUse = Field(..., description="Restrictions on vehicle use")
    authorizedDrivers: str = Field(..., description="Classes of persons allowed to drive")


class Vehicle(BaseModel):
    """Vehicle information"""
    registrationMark: str = Field(..., description="Vehicle license plate number")
    makeAndModel: str = Field(..., description="Manufacturer and specific model")
    yearOfManufacture: int = Field(..., description="Year of manufacture")
    chassisNumber: str = Field(..., description="Vehicle Identification Number (VIN)")
    engineNumber: Optional[str] = Field(default=None, description="Engine serial number")
    cubicCapacity: Optional[float] = Field(default=None, description="Engine size in cubic centimeters")
    seatingCapacity: int = Field(..., description="Number of seats including driver")
    bodyType: str = Field(..., description="Vehicle style (e.g., saloon, SUV)")
    estimatedValue: Optional[float] = Field(default=None, description="Insured's declared value in HKD")


class Levies(BaseModel):
    """Additional charges"""
    mib: Optional[float] = Field(default=None, description="MIB levy")
    ia: Optional[Union[float, str]] = Field(default=None, description="IA levy (can be number or 'INCLUDED')")


class PremiumAndDiscounts(BaseModel):
    """Premium and discount information"""
    premiumAmount: float = Field(..., description="Base premium in HKD")
    totalPayable: float = Field(..., description="Final amount including levies")
    noClaimDiscount: float = Field(..., description="Percentage discount for claim-free history")
    levies: Optional[Levies] = Field(default=None, description="Additional charges")


class PeriodOfInsurance(BaseModel):
    """Insurance period"""
    start: str = Field(..., description="Start date (format: DD/MM/YYYY)")
    end: str = Field(..., description="End date (format: DD/MM/YYYY)")


class InsurerAndPolicyDetails(BaseModel):
    """Insurer and policy information"""
    insurerName: str = Field(..., description="Company providing the policy")
    policyNumber: str = Field(..., description="Unique policy identifier")
    periodOfInsurance: PeriodOfInsurance = Field(..., description="Start and end dates")
    dateOfIssue: Optional[str] = Field(default=None, description="When the policy was issued (format: DD/MM/YYYY)")


class AdditionalEndorsements(BaseModel):
    """Additional endorsements and clauses"""
    endorsements: Optional[List[str]] = Field(default=None, description="List of special terms or exclusions")
    hirePurchaseMortgagee: Optional[str] = Field(default=None, description="Any financial interest parties")


class PolicyData(BaseModel):
    """Root model for complete policy data"""
    policyholder: Policyholder
    vehicle: Vehicle
    coverage: Coverage
    premiumAndDiscounts: PremiumAndDiscounts
    insurerAndPolicyDetails: InsurerAndPolicyDetails
    additionalEndorsements: Optional[AdditionalEndorsements] = Field(default=None)
