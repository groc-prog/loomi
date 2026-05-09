# pylint: disable=missing-class-docstring, missing-function-docstring

import functools
import importlib.util
import inspect
import pathlib
import sys
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Optional,
    Set,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
    overload,
)

import neo4j
import neo4j.graph

from loomi._internal.types import ModelType
from loomi._logger import LogContextKey, logger, scoped_log_ctx
from loomi.constants import ServerType
from loomi.exceptions import ClientError, ModelError
from loomi.graph.node import Node
from loomi.graph.path import Path
from loomi.graph.relationship import Relationship

T = TypeVar("T", bound=Union[neo4j.Driver, neo4j.AsyncDriver])
F = TypeVar("F", bound=Callable[..., Any])


class ClientConfiguration(TypedDict, total=False):
    """TypedDict for configuring Loomi client behavior."""

    serialize_nested: bool


def require_server_metadata(func: F) -> F:

    @functools.wraps(func)
    async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self._server_type is None:
            raise ClientError(f"Method '{func.__name__}' requires a connected server. ")
        return await func(self, *args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self._server_type is None:
            raise ClientError(f"Method '{func.__name__}' requires a connected server. ")
        return func(self, *args, **kwargs)

    if inspect.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    return cast(F, sync_wrapper)


class BaseClient(Generic[T]):
    _driver: T
    _server_type: Optional[ServerType]
    _server_version: Optional[Tuple[int, ...]]
    _models: Dict[str, ModelType]
    _configuration: ClientConfiguration

    def __init__(self, driver: T, **config):
        self._driver = driver
        self._server_type = None
        self._server_version = None
        self._models = {}
        self._configuration = ClientConfiguration(**config)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} driver={self._driver.__class__.__name__} "
            f"server_type={self._server_type} server_version={self._server_version}>"
        )

    @require_server_metadata
    def server_type(self) -> ServerType:
        """
        Returns the type of server the client is currently connected to.

        Returns:
            ServerType: The server type.
        """
        return cast(ServerType, self._server_type)

    @overload
    def register(self, *models: ModelType) -> None: ...

    @overload
    def register(self, models_dir: Union[str, pathlib.Path]) -> None: ...

    def register(  # pyright: ignore[reportInconsistentOverload]
        self, *models_or_path: Union[ModelType, str, pathlib.Path]
    ) -> None:
        """
        Registers models with the current client. Models which have not been registered can not be
        resolved from query results.

        Args:
            *models_or_path (Union[ModelType, str, pathlib.Path]): The models to register or
            a path to a directory containing the models to register.
        """

        if len(models_or_path) == 1 and isinstance(models_or_path[0], (str, pathlib.Path)):
            to_register: Set[ModelType] = set()
            path = pathlib.Path(models_or_path[0]).resolve()

            if path.is_dir():
                self._load_modules_from_dir(path)

                for root in (Node, Relationship):
                    for descendant in self._get_all_descendants(root):
                        if self._is_class_in_path(descendant, path):
                            if hasattr(descendant, "model_rebuild"):
                                descendant.model_rebuild(raise_errors=False)
                            to_register.add(descendant)

            self._register_models(*to_register)
        else:
            self._register_models(*cast(Iterable[ModelType], models_or_path))

    def _is_class_in_path(self, cls: Type, base_path: pathlib.Path) -> bool:
        try:
            source_file = pathlib.Path(inspect.getfile(cls)).resolve()
            return base_path in source_file.parents or source_file == base_path
        except (TypeError, OSError):
            return False

    def _register_models(self, *models: ModelType) -> None:
        with scoped_log_ctx(
            {
                LogContextKey.DRIVER: self._driver.__class__.__name__,
                LogContextKey.SERVER_TYPE: self._server_type,
            }
        ):
            for model in models:
                if not issubclass(model, (Node, Relationship)):
                    logger.warning(
                        "Invalid model %s provided during model registration, skipping",
                        model,
                    )
                    continue

                # In most cases, the hash should always be initialized, but there can be some issues
                # when using forward refs
                if model._hash is None:
                    raise ModelError(
                        f"Hash on model {model.__name__} is not initialized. Maybe you forgot to "
                        f"call {model.model_rebuild.__name__}?"
                    )

                logger.debug("Registering model %s with client %s", model, self)
                self._models[model._hash] = model

    def _get_all_descendants(self, cls: Type) -> Iterable[Type]:
        for subclass in cls.__subclasses__():
            subclass.model_rebuild()

            yield subclass
            yield from self._get_all_descendants(subclass)

    def _load_modules_from_dir(self, path: pathlib.Path) -> None:
        already_loaded_files = {
            pathlib.Path(cast(str, mod.__file__)).resolve()
            for mod in list(sys.modules.values())
            if getattr(mod, "__file__", None)
        }

        for py_file in path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            resolved_file = py_file.resolve()
            if resolved_file in already_loaded_files:
                logger.debug("Skipping %s, already loaded in sys.modules", py_file)
                continue

            mod_name = f"loomi_model_discovery{py_file.stem}_{hash(str(resolved_file)) % 10**4}"
            spec = importlib.util.spec_from_file_location(mod_name, resolved_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                try:
                    spec.loader.exec_module(module)
                    # Add to set so we don't load the same file twice in this loop
                    already_loaded_files.add(resolved_file)
                except Exception as e:
                    logger.error("Failed to load module %s: %s", py_file, e)
                    del sys.modules[mod_name]

    def _extract_version(self, version: str) -> None:
        self._server_version = tuple(int(part) for part in version.split("."))

    def _transform_entity(self, entity: Any) -> Any:
        with scoped_log_ctx(
            {
                LogContextKey.DRIVER: self._driver.__class__.__name__,
                LogContextKey.SERVER_TYPE: self._server_type,
            }
        ):
            if isinstance(entity, (neo4j.graph.Node, neo4j.graph.Relationship)):
                return self._entity_to_model(entity)
            if isinstance(entity, neo4j.graph.Path):
                logger.debug("Transforming nodes and relationships from path %s", entity)
                return Path(
                    self,
                    tuple(self._entity_to_model(node) for node in entity.nodes),
                    tuple(
                        self._entity_to_model(relationship) for relationship in entity.relationships
                    ),
                    entity.graph,
                )

            logger.debug("Entity %s is a primitive value, skipping transformation", entity)
            return entity

    @overload
    def _entity_to_model(self, entity: neo4j.graph.Node) -> Union[Node, neo4j.graph.Node]: ...

    @overload
    def _entity_to_model(
        self, entity: neo4j.graph.Relationship
    ) -> Union[Relationship, neo4j.graph.Relationship]: ...

    def _entity_to_model(
        self, entity: Union[neo4j.graph.Node, neo4j.graph.Relationship]
    ) -> Union[Node, Relationship, neo4j.graph.Node, neo4j.graph.Relationship]:
        model_hash = (
            Node._generate_hash(list(entity.labels))
            if isinstance(entity, neo4j.graph.Node)
            else Relationship._generate_hash(entity.type)
        )

        if model_hash not in self._models:
            logger.warning(
                "No model with hash %s registered with client. Record will not be transformed",
                model_hash,
            )
            return entity

        model = self._models[model_hash]
        logger.debug("Transforming %s to model %s", entity, model.__name__)

        instance = model._deserialize(
            dict(entity), self._server_type or ServerType.NEO4J, self._configuration
        )
        instance._id = entity.id
        instance._element_id = entity.element_id

        return instance

    def _relationship_type_to_model(self, type_: str) -> Optional[Type[Relationship]]:
        with scoped_log_ctx(
            {
                LogContextKey.DRIVER: self._driver.__class__.__name__,
                LogContextKey.SERVER_TYPE: self._server_type,
            }
        ):
            model_hash = Relationship._generate_hash(type_)

            if model_hash not in self._models:
                logger.warning(
                    "No model with hash %s registered with client. Record will not be transformed",
                    model_hash,
                )
                return None

            return cast(Type[Relationship], self._models[model_hash])
