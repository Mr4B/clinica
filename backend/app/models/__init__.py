# 1) base comuni
from .common import Message, Token, TokenPayload, NewPassword
from .tables import Role, User, Structure, Dossier, Patient, ModuleEntry, ModuleCatalog, AuditLog
from .role import RoleCreate, RoleUpdate, RolePublic, RolesPublic, AssignRoleIn

# 2) entità senza dipendenze incrociate
from .patient import PatientCreate, PatientUpdate, PatientListResponse, PatientResponse, PatientBase
from .module import (EntryCreate, EntryUpdate, EntryResponse, EntryListResponse, ModuleInfo,
                        ModuleCatalogCreate, ModuleCatalogUpdate, ModuleCatalogResponse, ModuleCatalogListResponse)

# 3) structure poi user poi dossier
from .structure import StructureCreate, StructureUpdate, StructuresPublic, StructureBase
from .user import UserCreate, UserRegister, UserUpdate, UserUpdateMe, UpdatePassword, UserPublic, UsersPublic
from .dossier import DossierCreate, DossierBase, DossierUpdate, DossierResponse, DossierDetailResponse, DossierListResponse

# from .audit import AuditLog

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
    "Patient", "PatientCreate", "PatientUpdate", "PatientListResponse", "PatientResponse", "PatientBase",
    # audit
    "AuditLog"
]
