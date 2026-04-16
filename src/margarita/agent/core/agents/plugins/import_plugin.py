import ast
import importlib
import importlib.util
import os
import sys

from margarita.agent.core.agents.models import ExecutionModel


class ImportPlugin:
    """Handles import statements found in .mgx files.

    Validates and executes dynamic Python imports required by agent runs.
    """

    @staticmethod
    def _load_package_from_cwd(top_level: str, fullname: str | None = None):
        """Load a package (and optional dotted submodule) from the current working directory.

        Registers loaded modules in sys.modules. Raises ModuleNotFoundError if not found.
        """
        cwd = os.getcwd()
        pkg_dir = os.path.join(cwd, top_level)
        init_py = os.path.join(pkg_dir, "__init__.py")
        if not os.path.isdir(pkg_dir) or not os.path.isfile(init_py):
            raise ModuleNotFoundError(f"Package {top_level!r} not found in cwd")

        # load top-level package
        spec = importlib.util.spec_from_file_location(top_level, init_py)
        if spec is None or spec.loader is None:
            raise ModuleNotFoundError(f"Cannot create spec to load package {top_level!r} from cwd")
        pkg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pkg)  # type: ignore
        sys.modules[top_level] = pkg

        # if fullname requests a submodule (e.g. top.sub.mod), walk and load pieces
        if fullname and fullname != top_level:
            parts = fullname.split(".")[1:]
            base_dir = pkg_dir
            cur_name = top_level
            for part in parts:
                cur_name = f"{cur_name}.{part}"
                candidate_pkg = os.path.join(base_dir, part)
                candidate_init = os.path.join(candidate_pkg, "__init__.py")
                candidate_py = os.path.join(base_dir, part + ".py")

                if os.path.isfile(candidate_init):
                    spec = importlib.util.spec_from_file_location(cur_name, candidate_init)
                    if spec is None or spec.loader is None:
                        raise ModuleNotFoundError(f"Cannot create spec for {cur_name!r}")
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)  # type: ignore
                    sys.modules[cur_name] = mod
                    base_dir = candidate_pkg
                elif os.path.isfile(candidate_py):
                    spec = importlib.util.spec_from_file_location(cur_name, candidate_py)
                    if spec is None or spec.loader is None:
                        raise ModuleNotFoundError(f"Cannot create spec for {cur_name!r}")
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)  # type: ignore
                    sys.modules[cur_name] = mod
                    base_dir = os.path.dirname(candidate_py)
                else:
                    raise ModuleNotFoundError(f"Submodule {cur_name!r} not found in cwd package")

            return sys.modules.get(fullname)

        return pkg

    @staticmethod
    def _maybe_add_active_venv_sitepackages() -> bool:
        """If a virtualenv/conda prefix is active, add its site-packages to sys.path.

        Returns True if a path was added, False otherwise.

        This looks for common site-packages locations for venv/conda and inserts the
        first candidate found at the front of sys.path so subsequent import attempts
        may succeed using the activated environment.
        """
        venv = os.environ.get("VIRTUAL_ENV") or os.environ.get("CONDA_PREFIX")
        if not venv:
            return False

        # Common candidate locations
        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        candidates = [
            os.path.join(venv, "lib", pyver, "site-packages"),  # Unix venv
            os.path.join(venv, "Lib", "site-packages"),  # Windows venv
            os.path.join(venv, "site-packages"),  # fallback
        ]
        for p in candidates:
            if os.path.isdir(p) and p not in sys.path:
                sys.path.insert(0, p)
                return True
        return False

    @staticmethod
    def execute_import(import_stmt: str, execution_model: ExecutionModel) -> dict:
        """Execute an import statement and update the provided globals dictionary.

        Args:
            import_stmt (str): The import statement to execute.
            execution_model (ExecutionModel): The execution model for the current agent run.
        """
        tree = ast.parse(import_stmt)

        for node in tree.body:
            module = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        module = importlib.import_module(str(alias.name))
                    except ModuleNotFoundError:
                        # first try active venv/conda site-packages if present
                        try:
                            added = ImportPlugin._maybe_add_active_venv_sitepackages()
                        except Exception:
                            added = False

                        if added:
                            try:
                                module = importlib.import_module(str(alias.name))
                            except ModuleNotFoundError:
                                module = None
                            except Exception as e:
                                execution_model.add_log(
                                    f"Error importing {alias.name} after adding venv site-packages: {e}"
                                )
                                execution_model.add_import_error(str(e))
                                continue

                        if module is None:
                            # fall back to loading package from the current working directory
                            top = alias.name.split(".")[0]
                            try:
                                module = ImportPlugin._load_package_from_cwd(top, alias.name)
                            except ModuleNotFoundError as e:
                                execution_model.add_log(f"Module not found: {alias.name}")
                                execution_model.add_import_error(str(e))
                                continue
                            except Exception as e:
                                execution_model.add_log(f"Error loading {alias.name} from cwd: {e}")
                                execution_model.add_import_error(str(e))
                                continue
                    except Exception as e:
                        execution_model.add_log(f"Error importing {alias.name}: {e}")
                        execution_model.add_import_error(str(e))
                        continue

                    name = alias.asname or alias.name
                    execution_model.globals_dict[name] = module

            elif isinstance(node, ast.ImportFrom):
                if not node.module:
                    execution_model.add_log("Empty module name in ImportFrom")
                    execution_model.add_import_error("Empty module name in ImportFrom")
                    continue

                module = None
                try:
                    module = importlib.import_module(str(node.module))
                except ModuleNotFoundError:
                    # try active venv/conda site-packages first
                    try:
                        added = ImportPlugin._maybe_add_active_venv_sitepackages()
                    except Exception:
                        added = False

                    if added:
                        try:
                            module = importlib.import_module(str(node.module))
                        except ModuleNotFoundError:
                            module = None
                        except Exception as e:
                            execution_model.add_log(
                                f"Error importing {node.module} after adding venv site-packages: {e}"
                            )
                            execution_model.add_import_error(str(e))
                            continue

                    if module is None:
                        top = node.module.split(".")[0]
                        try:
                            ImportPlugin._load_package_from_cwd(top, node.module)
                            module = importlib.import_module(str(node.module))
                        except ModuleNotFoundError as e:
                            execution_model.add_log(f"Module not found: {node.module}")
                            execution_model.add_import_error(str(e))
                            continue
                        except Exception as e:
                            execution_model.add_log(f"Error importing {node.module}: {e}")
                            execution_model.add_import_error(str(e))
                            continue
                except Exception as e:
                    execution_model.add_log(f"Error importing {node.module}: {e}")
                    execution_model.add_import_error(str(e))
                    continue

                for alias in node.names:
                    try:
                        obj = getattr(module, alias.name)
                        name = alias.asname or alias.name
                        execution_model.globals_dict[name] = obj
                    except AttributeError as e:
                        execution_model.add_log(f"{alias.name} not found in {node.module}")
                        execution_model.add_import_error(str(e))
                    except Exception as e:
                        execution_model.add_log(
                            f"Error loading {alias.name} from {node.module}: {e}"
                        )
                        execution_model.add_import_error(str(e))
            else:
                execution_model.add_log("Only import statements are allowed")
                execution_model.add_import_error("Only import statements are allowed")

        return execution_model.globals_dict
