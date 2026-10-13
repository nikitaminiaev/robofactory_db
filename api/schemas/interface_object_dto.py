from typing import Optional, Dict
from pydantic import BaseModel


class InterfaceObjectDTO(BaseModel):
    id: str
    name: str
    direction: str = "bidirectional"
    physical_form: Optional[str] = None
    parameters: Optional[Dict] = None
    is_mandatory: bool = True
    is_service: bool = False
    module_id: Optional[str] = None
    description: Optional[str] = None
    ttx: Optional[str] = None
    coordinates: Optional[Dict] = None
    created_ts: Optional[str] = None
    updated_ts: Optional[str] = None


class InterfaceCreateDTO(BaseModel):
    name: str
    direction: str = "bidirectional"
    physical_form: Optional[str] = None
    parameters: Optional[Dict] = None
    is_mandatory: bool = True
    is_service: bool = False
    description: Optional[str] = None
    ttx: Optional[str] = None


class InterfaceUpdateDTO(BaseModel):
    name: Optional[str] = None
    direction: Optional[str] = None
    physical_form: Optional[str] = None
    parameters: Optional[Dict] = None
    is_mandatory: Optional[bool] = None
    is_service: Optional[bool] = None
    description: Optional[str] = None
    ttx: Optional[str] = None


class InterfaceMappingDTO(BaseModel):
    id: str
    module_id: str
    role_port_id: str
    interface_id: str
    interface_name: Optional[str] = None
    role_port_name: Optional[str] = None
    role_name: Optional[str] = None
    role_id: Optional[str] = None
    created_ts: Optional[str] = None


class InterfaceMappingCreateDTO(BaseModel):
    role_port_id: str
    interface_id: str
