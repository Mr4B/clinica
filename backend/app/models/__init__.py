# Import models so Alembic sees the tables in SQLModel.metadata
from .role import Role, RoleCreate, RoleUpdate, RolePublic, RolesPublic, AssignRoleIn
from .user import User, UserCreate, UserRegister, UserUpdate, UserUpdateMe, UpdatePassword, UserPublic, UsersPublic
from .common import Message, Token, TokenPayload, NewPassword
from .structure import Structure, StructureCreate, StructureUpdate, StructuresPublic, StructureBase
from .module import (ModuleEntry, EntryCreate, EntryUpdate, EntryResponse, EntryListResponse, ModuleInfo,
ModuleCatalog, ModuleCatalogCreate, ModuleCatalogUpdate, ModuleCatalogResponse, ModuleCatalogListResponse)
from .dossier import Dossier, DossierCreate, DossierBase, DossierUpdate, DossierResponse, DossierDetailResponse, DossierListResponse
from .patient import Patient, PatientCreate, PatientUpdate, PatientListResponse, PatientResponse, PatientBase

__all__ = [
    # role
    "Role", "RoleCreate", "RoleUpdate", "RolePublic", "RolesPublic", "AssignRoleIn",
    # user
    "User", "UserCreate", "UserRegister", "UserUpdate", "UserUpdateMe",
    "UpdatePassword", "UserPublic", "UsersPublic",
    # common
    "Message", "Token", "TokenPayload", "NewPassword",
    # structure
    "Structure", "StructureCreate", "StructureUpdate",  "StructuresPublic", "StructureBase",
    # module
    "ModuleEntry", "EntryCreate", "EntryUpdate", "EntryResponse", "EntryListResponse", "ModuleInfo",
    "ModuleCatalog", "ModuleCatalogCreate", "ModuleCatalogUpdate", "ModuleCatalogResponse", "ModuleCatalogListResponse",
    # dossier
    "Dossier", "DossierCreate", "DossierBase", "DossierUpdate", "DossierResponse", "DossierDetailResponse", "DossierListResponse",
    # patient
    "Patient", "PatientCreate", "PatientUpdate", "PatientListResponse", "PatientResponse", "PatientBase"
]
