from .sanitariaInfermieristica import modules_sanInf

all_modules = []
all_modules.extend(modules_sanInf)

# tira in automatico le variabili che iniziano in modules
# for _, module_name, _ in pkgutil.iter_modules(__path__):
#     subpkg = importlib.import_module(f"{__name__}.{module_name}")
#     for attr in dir(subpkg):
#         if attr.startswith("modules_"):
#             all_modules.extend(getattr(subpkg, attr))

__all__ = [m.__name__ for m in all_modules]
globals().update({m.__name__: m for m in all_modules})